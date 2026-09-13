"""Smoke-test parameter recovery (N_SAMPLES=100, BURN=20).

Outputs go to results/parameter_recovery/_test_runs/ and never overwrite
production CSVs under results/parameter_recovery/<tag>/.

Usage (from repo root or hddm_analysis/notebooks/):
D:\\ProgramData\\envs\\hddm\\python.exe hddm_analysis/scripts/run_parameter_recovery_test.py
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

from nc_io import from_netcdf as load_idata
import hddm
import numpy as np
import pandas as pd
from hddm.generate import gen_rts
from joblib import Parallel, delayed
from scipy import stats

# ---------------------------------------------------------------------------
# Paths — resolve repo root whether launched from notebooks/ or repo root
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
HDDM_ANALYSIS = SCRIPT_DIR.parent

DATA_DIR = HDDM_ANALYSIS / "data"
RESULTS_DIR = HDDM_ANALYSIS / "results"
MODEL_DIR = HDDM_ANALYSIS / "models" / "transition_prob_duration_10000samples"

# ---------------------------------------------------------------------------
# Test configuration (does not touch production outputs)
# ---------------------------------------------------------------------------
TEST_RUN = True
N_SAMPLES = 100
BURN = 20
N_REPS = 30
N_CHAINS = 4
CHAIN_PARALLEL = True
RECOVERY_SEED = 12345
CHECKPOINT_EVERY_REPS = 5
QUIET_RECOVERY_LOG = False

DEPENDS_ON_RECOVERY = {
    "v": ["transition", "prob", "long_short"],
    "a": ["transition", "prob", "long_short"],
}
INCLUDE_RECOVERY = ["v", "a", "t"]
RECOVERY_REFERENCE_STEM = "hddm_va_vat"
RECOVERY_RANGE_EXPAND = 0.2
IS_GROUP_MODEL = True

_RECOVERY_PARAM_ORDER = ("v", "a", "t", "z")


def recovery_file_tag(depends_on: dict, include: list) -> str:
    unk = (set(depends_on) | set(include)) - set(_RECOVERY_PARAM_ORDER)
    if unk:
        raise ValueError(f"Unknown param name(s) {unk} for auto tag.")
    dep = "".join(p for p in _RECOVERY_PARAM_ORDER if p in depends_on)
    inc = "".join(p for p in _RECOVERY_PARAM_ORDER if p in include)
    return f"{dep}_{inc}"


RECOVERY_FILE_TAG = recovery_file_tag(DEPENDS_ON_RECOVERY, INCLUDE_RECOVERY)
TEST_SUFFIX = f"{N_SAMPLES}samples_{BURN}burn"
OUT_DIR = RESULTS_DIR / "parameter_recovery" / "_test_runs" / f"{RECOVERY_FILE_TAG}_{TEST_SUFFIX}"
OUT_DIR.mkdir(parents=True, exist_ok=True)

REPS_N_JOBS = max(1, min(N_REPS, os.cpu_count() or 1))
PARTIAL_CSV = OUT_DIR / f"parameter_recovery_partial_{RECOVERY_FILE_TAG}_{TEST_SUFFIX}.csv"
PROGRESS_PATH = OUT_DIR / f"parameter_recovery_progress_{RECOVERY_FILE_TAG}_{TEST_SUFFIX}.txt"


def flip_errors(data: pd.DataFrame) -> pd.DataFrame:
    if np.any(data["rt"] < 0):
        return data
    out = data.copy()
    out.loc[out["response"] != 1, "rt"] = -out.loc[out["response"] != 1, "rt"]
    return out


def load_hddm_data() -> pd.DataFrame:
    min_rt_ms = 150
    trials = pd.read_csv(DATA_DIR / "trials_hddm_ready.tsv", sep="\t")
    trials = trials.loc[trials["rt_ms"] > min_rt_ms].copy()
    hddm_data = trials.copy()
    hddm_data["response"] = hddm_data["acc"].astype(int)
    hddm_data["rt"] = hddm_data["rt_ms"] / 1000.0
    hddm_data = hddm_data[["subj_idx", "transition", "prob", "long_short", "response", "rt"]]
    return flip_errors(hddm_data)


def _posterior_var_names_for_param(par, depends_on, all_names):
    if par in depends_on:
        return [n for n in all_names if n.startswith(f"{par}(")]
    selected = [n for n in all_names if n == par]
    if not selected:
        selected = [n for n in all_names if str(n).startswith(par) and "(" not in str(n)]
    if not selected:
        selected = [n for n in all_names if n.startswith(f"{par}(")]
    return selected


def _true_uniform_ranges_from_posterior(idata, include, depends_on, expand):
    posterior = idata.posterior
    all_names = [str(v) for v in posterior.data_vars]
    ranges, raw_mm = {}, {}
    for par in include:
        selected = _posterior_var_names_for_param(par, depends_on, all_names)
        if not selected:
            raise ValueError(
                f"No posterior variables for '{par}'. Sample names: {all_names[:40]}"
            )
        chunks = []
        for n in selected:
            x = np.asarray(posterior[n].values, dtype=float).ravel()
            x = x[np.isfinite(x)]
            if x.size:
                chunks.append(x)
        if not chunks:
            raise ValueError(f"No finite posterior samples for '{par}' (vars {selected})")
        samples = np.concatenate(chunks)
        lo, hi = float(np.min(samples)), float(np.max(samples))
        raw_mm[par] = (lo, hi)
        span = hi - lo
        if span <= 0:
            pad = max(abs(lo), 1e-6) * expand
            lo, hi = lo - pad, hi + pad
        else:
            m = span * expand
            lo, hi = lo - m, hi + m
        ranges[par] = (lo, hi)
    return ranges, raw_mm


def discover_cond_str_fn(hddm_df, idata=None):
    cols = ["long_short", "prob", "transition"]
    sample = hddm_df.iloc[0]
    order = cols
    if idata is not None and hasattr(idata, "posterior"):
        vkey = next(
            (str(k) for k in idata.posterior.data_vars if str(k).startswith("v(")),
            None,
        )
        if vkey is not None:
            inner = vkey.split("(", 1)[1].rstrip(")").split(".")
            order = []
            used = set()
            for tok in inner:
                for c in cols:
                    if c in used:
                        continue
                    if str(sample[c]) == tok:
                        order.append(c)
                        used.add(c)
                        break
            if len(order) != 3:
                order = cols
        else:
            order = cols

    def cond_str(row):
        return ".".join(str(row[c]) for c in order)

    return cond_str, order


def sample_ground_truth(cond_list, rng, true_uniform_ranges):
    true = {}
    for par in INCLUDE_RECOVERY:
        lo, hi = true_uniform_ranges[par]
        if par in DEPENDS_ON_RECOVERY:
            true[par] = {c: float(rng.uniform(lo, hi)) for c in cond_list}
        else:
            true[par] = float(rng.uniform(lo, hi))
    return true


def simulate_hddm_df(template_df, true_params, cond_fn):
    rts, resps = [], []
    for _, row in template_df.iterrows():
        c = cond_fn(row)
        kw = {"sv": 0, "sz": 0, "st": 0}
        for par in INCLUDE_RECOVERY:
            if par in DEPENDS_ON_RECOVERY:
                kw[par] = true_params[par][c]
            else:
                kw[par] = true_params[par]
        d = gen_rts(size=1, method="cdf", **kw)
        rts.append(float(d["rt"].iloc[0]))
        resps.append(int(d["response"].iloc[0]))
    sim = template_df.copy()
    sim["rt"] = rts
    sim["response"] = resps
    return hddm.utils.flip_errors(sim)


def posterior_means_from_traces(traces_df):
    return traces_df.mean(axis=0)


def trace_scalar_group_mean(pm, basename):
    cols = [
        k
        for k in pm.index
        if k == basename or (str(k).startswith(basename) and "(" not in str(k))
    ]
    if not cols:
        cols = [k for k in pm.index if str(k).startswith(f"{basename}(")]
    if not cols:
        raise KeyError(f"No trace for '{basename}'. Sample columns: {list(pm.index)[:40]}")
    return float(np.mean([pm[k] for k in cols]))


def recovery_one_rep(
    template_df,
    cond_fn,
    cond_list,
    rng,
    true_uniform_ranges,
    chain_parallel=None,
    n_samples=None,
    burn=None,
    n_chains=None,
):
    chain_parallel = CHAIN_PARALLEL if chain_parallel is None else chain_parallel
    n_samples = N_SAMPLES if n_samples is None else n_samples
    burn = BURN if burn is None else burn
    n_chains = N_CHAINS if n_chains is None else n_chains

    true_params = sample_ground_truth(cond_list, rng, true_uniform_ranges)
    sim_df = simulate_hddm_df(template_df, true_params, cond_fn)

    m = hddm.HDDM(
        sim_df,
        depends_on=DEPENDS_ON_RECOVERY,
        include=INCLUDE_RECOVERY,
        is_group_model=IS_GROUP_MODEL,
        p_outlier=0.05,
    )
    m.find_starting_values()
    m.sample(n_samples, burn=burn, chains=n_chains, parallel=chain_parallel, verbose=0)
    pm = posterior_means_from_traces(m.get_traces())

    tru_by_cell = {p: [] for p in DEPENDS_ON_RECOVERY}
    rec_by_cell = {p: [] for p in DEPENDS_ON_RECOVERY}
    for c in cond_list:
        for par in DEPENDS_ON_RECOVERY:
            key = f"{par}({c})"
            tru_by_cell[par].append(true_params[par][c])
            rec_by_cell[par].append(float(pm[key]))

    scalar_true, scalar_rec = {}, {}
    for par in INCLUDE_RECOVERY:
        if par in DEPENDS_ON_RECOVERY:
            continue
        scalar_true[par] = true_params[par]
        scalar_rec[par] = trace_scalar_group_mean(pm, par)

    return true_params, tru_by_cell, rec_by_cell, scalar_true, scalar_rec


def _rows_for_rep(rep_id, cond_list, tru_by_cell, rec_by_cell, scalar_true, scalar_rec):
    rows = []
    for i, c in enumerate(cond_list):
        row = {"rep": rep_id, "cell": c}
        for par in INCLUDE_RECOVERY:
            tc, rc = f"true_{par}", f"rec_{par}"
            if par in DEPENDS_ON_RECOVERY:
                row[tc] = tru_by_cell[par][i]
                row[rc] = rec_by_cell[par][i]
            else:
                row[tc] = np.nan
                row[rc] = np.nan
        rows.append(row)

    for par in INCLUDE_RECOVERY:
        if par in DEPENDS_ON_RECOVERY:
            continue
        row = {"rep": rep_id, "cell": f"__{par}__"}
        for p2 in INCLUDE_RECOVERY:
            tc, rc = f"true_{p2}", f"rec_{p2}"
            if p2 == par:
                row[tc] = scalar_true[par]
                row[rc] = scalar_rec[par]
            else:
                row[tc] = np.nan
                row[rc] = np.nan
        rows.append(row)
    return rows


def _recovery_rep_worker(
    rep_id,
    template_df,
    cond_fn,
    cond_list,
    true_uniform_ranges,
    chain_parallel,
    seed_base,
):
    old_cwd = os.getcwd()
    workdir = tempfile.mkdtemp(prefix=f"hddm_recovery_rep{rep_id}_")
    try:
        os.chdir(workdir)
        t0 = time.perf_counter()
        rng = np.random.default_rng(seed_base + rep_id)
        _, tru_bc, rec_bc, s_true, s_rec = recovery_one_rep(
            template_df,
            cond_fn,
            cond_list,
            rng,
            true_uniform_ranges,
            chain_parallel=chain_parallel,
        )
        rows = _rows_for_rep(rep_id, cond_list, tru_bc, rec_bc, s_true, s_rec)
        elapsed = time.perf_counter() - t0
        return rep_id, rows, elapsed
    finally:
        try:
            os.chdir(old_cwd)
        except OSError:
            pass
        shutil.rmtree(workdir, ignore_errors=True)


def _write_progress(done, total, mode, extra=""):
    pct = 100.0 * done / max(total, 1)
    PROGRESS_PATH.write_text(
        f"done={done}/{total} ({pct:.1f}%) | mode={mode} | tag={RECOVERY_FILE_TAG} | "
        f"test={TEST_SUFFIX} | out={OUT_DIR} {extra}".strip(),
        encoding="utf-8",
    )


def corr_report(x, y, name):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return name, np.nan, np.nan
    r, p = stats.pearsonr(x[mask], y[mask])
    print(f"{name}: Pearson r = {r:.3f}, p = {p:.2e}, n = {mask.sum()}")
    return name, r, p


def main():
    ref_nc = MODEL_DIR / f"{RECOVERY_REFERENCE_STEM}_combined.nc"
    if not ref_nc.is_file():
        sys.exit(f"Missing reference posterior: {ref_nc}")

    print(f"TEST_RUN={TEST_RUN}")
    print(f" N_SAMPLES={N_SAMPLES}, BURN={BURN}, N_REPS={N_REPS}, N_CHAINS={N_CHAINS}")
    print(f" Reference: {ref_nc}")
    print(f" Output dir (no overwrite of production): {OUT_DIR}")
    print(f" Parallel reps: REPS_N_JOBS={REPS_N_JOBS}")

    id_ref = load_idata(ref_nc)
    true_uniform_ranges, raw_mm = _true_uniform_ranges_from_posterior(
        id_ref, INCLUDE_RECOVERY, DEPENDS_ON_RECOVERY, RECOVERY_RANGE_EXPAND
    )
    for par in INCLUDE_RECOVERY:
        a, b = raw_mm[par]
        lo, hi = true_uniform_ranges[par]
        print(f" {par}: posterior [{a:.4f}, {b:.4f}] -> sim range [{lo:.4f}, {hi:.4f}]")

    hddm_data = load_hddm_data()
    print(f" hddm_data: {hddm_data.shape}")

    cond_fn, _order = discover_cond_str_fn(hddm_data, id_ref)
    cond_list = sorted(hddm_data.apply(cond_fn, axis=1).unique())
    chain_parallel_effective = CHAIN_PARALLEL if REPS_N_JOBS == 1 else False

    _write_progress(0, N_REPS, "sequential" if REPS_N_JOBS <= 1 else "parallel")

    if REPS_N_JOBS <= 1:
        rng = np.random.default_rng(RECOVERY_SEED)
        all_rows = []
        for rep in range(N_REPS):
            t0 = time.perf_counter()
            _, tru_bc, rec_bc, s_true, s_rec = recovery_one_rep(
                hddm_data,
                cond_fn,
                cond_list,
                rng,
                true_uniform_ranges,
                chain_parallel=chain_parallel_effective,
            )
            all_rows.extend(_rows_for_rep(rep, cond_list, tru_bc, rec_bc, s_true, s_rec))
            elapsed = time.perf_counter() - t0
            print(f" rep {rep + 1}/{N_REPS} done ({elapsed:.1f}s)")
            if (rep + 1) % CHECKPOINT_EVERY_REPS == 0 or (rep + 1) == N_REPS:
                pd.DataFrame(all_rows).to_csv(PARTIAL_CSV, index=False, encoding="utf-8-sig")
                _write_progress(rep + 1, N_REPS, "sequential", extra=f"| rows={len(all_rows)}")
    else:
        results = Parallel(n_jobs=REPS_N_JOBS, backend="loky", verbose=10)(
            delayed(_recovery_rep_worker)(
                rep,
                hddm_data,
                cond_fn,
                cond_list,
                true_uniform_ranges,
                chain_parallel_effective,
                RECOVERY_SEED,
            )
            for rep in range(N_REPS)
        )
        results = sorted(results, key=lambda x: x[0])
        all_rows = []
        for rep_id, rows, elapsed in results:
            all_rows.extend(rows)
            print(f" rep {rep_id + 1}/{N_REPS} done ({elapsed:.1f}s)")
        pd.DataFrame(all_rows).to_csv(PARTIAL_CSV, index=False, encoding="utf-8-sig")
        _write_progress(N_REPS, N_REPS, "parallel", extra=f"| rows={len(all_rows)}")

    rec_df = pd.DataFrame(all_rows)
    rec_path = OUT_DIR / f"parameter_recovery_{RECOVERY_FILE_TAG}_{TEST_SUFFIX}_by_rep.csv"
    rec_df.to_csv(rec_path, index=False, encoding="utf-8-sig")
    print("Saved:", rec_path)
    print("Progress file:", PROGRESS_PATH)

    scalar_cells = [f"__{p}__" for p in INCLUDE_RECOVERY if p not in DEPENDS_ON_RECOVERY]
    cell_df = rec_df[~rec_df["cell"].isin(scalar_cells)].copy()

    summary = []
    for par in INCLUDE_RECOVERY:
        tx, ty = f"true_{par}", f"rec_{par}"
        if par in DEPENDS_ON_RECOVERY:
            summary.append(corr_report(cell_df[tx], cell_df[ty], f"{par} (cells x reps)"))
        else:
            sdf = rec_df[rec_df["cell"] == f"__{par}__"]
            summary.append(corr_report(sdf[tx], sdf[ty], f"{par} (scalar per rep)"))

    summary_df = pd.DataFrame(summary, columns=["parameter", "pearson_r", "p_value"])
    corr_path = OUT_DIR / f"parameter_recovery_{RECOVERY_FILE_TAG}_{TEST_SUFFIX}_correlations.csv"
    summary_df.to_csv(corr_path, index=False, encoding="utf-8-sig")
    print("Saved:", corr_path)


if __name__ == "__main__":
    main()
