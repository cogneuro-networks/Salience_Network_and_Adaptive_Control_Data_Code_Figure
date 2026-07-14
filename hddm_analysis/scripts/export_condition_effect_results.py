"""Regenerate condition-effect analysis CSVs (requires local .nc with subject nodes).

Usage (from hddm_analysis/):
python scripts/export_condition_effect_results.py
python scripts/export_condition_effect_results.py --nc path/to/hddm_va_vat_combined.nc
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import defaultdict

import arviz as az
import numpy as np
import pandas as pd
from scipy import stats

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from posterior_contrasts import flexible_trace_analysis, results_to_rows  # noqa: E402
from nc_io import from_netcdf as load_idata  # noqa: E402

DEFAULT_NC = os.path.join(
    ROOT,
    "models",
    "transition_prob_duration_10000samples",
    "hddm_va_vat_combined.nc",
)
COND_EFFECT_DIR = os.path.join(ROOT, "results", "condition_effects")

FACTORS = {
    "duration": ["Long", "Short"],
    "prob": ["prob_diff", "prob_same"],
    "transition": ["flexibility", "stability"],
}
FLUX_FACTORS = {
    "prob": ["prob_diff", "prob_same"],
    "transition": ["flexibility", "stability"],
}
SEP = "."
MODEL = "hddm_va_vat"
PARAMS = ["v", "a"]


def _has_subject_nodes(idata: az.InferenceData) -> bool:
    return any("_subj" in str(k) for k in idata.posterior.data_vars)


def _cell_str(d, p, t):
    return SEP.join([d, p, t])


def _subj_means_hddm_named(post, param, condition_str):
    pat = re.compile(
        "^"
        + re.escape(param)
        + r"_subj\("
        + re.escape(condition_str)
        + r"\)\.(\d+)$"
    )
    out = {}
    for k in post.data_vars:
        m = pat.match(str(k))
        if not m:
            continue
        sid = int(m.group(1))
        x = np.asarray(post[k].values, dtype=float)
        out[sid] = float(np.mean(x, axis=tuple(range(x.ndim))))
    return out


def _subj_means_legacy(post, param, condition_str):
    stem = f"{param}({condition_str})"
    keys = [str(k) for k in post.data_vars]
    out = {}

    sk = f"{stem}_subj"
    if sk in post:
        x = np.asarray(post[sk].values, dtype=float)
        if x.ndim >= 3:
            m = np.mean(x, axis=tuple(range(x.ndim - 1)))
            return {i: float(m[i]) for i in range(m.shape[-1])}
        if x.ndim == 2:
            m = np.mean(x, axis=0)
            return {i: float(m[i]) for i in range(len(m))}

    idx_to_key = {}
    for k in keys:
        m = re.fullmatch(re.escape(stem) + r"_subj\.(\d+)", k)
        if m:
            idx_to_key[int(m.group(1))] = k
    for i in sorted(idx_to_key):
        v = np.asarray(post[idx_to_key[i]].values, dtype=float)
        out[i] = float(np.mean(v, axis=tuple(range(v.ndim))))
    return out


def _subj_means(post, param, condition_str):
    d = _subj_means_hddm_named(post, param, condition_str)
    if d:
        return d
    d = _subj_means_legacy(post, param, condition_str)
    if d:
        return d
    raise KeyError(f"No subject traces for {param}_subj({condition_str}).<id>")


def _delta_short_minus_long(idata, param):
    post = idata.posterior
    sums = defaultdict(list)
    for p in FLUX_FACTORS["prob"]:
        for t in FLUX_FACTORS["transition"]:
            ds = _subj_means(post, param, _cell_str("Short", p, t))
            dl = _subj_means(post, param, _cell_str("Long", p, t))
            for sid in set(ds) & set(dl):
                sums[sid].append(ds[sid] - dl[sid])
    if not sums:
        raise ValueError("No overlapping Short/Long subject pairs in any cell.")
    return {sid: float(np.mean(vals)) for sid, vals in sums.items()}


def export_contrasts(idata: az.InferenceData, out_dir: str) -> pd.DataFrame:
    os.makedirs(out_dir, exist_ok=True)
    frames = []
    for param in PARAMS:
        results = flexible_trace_analysis(idata, param=param, factors=FACTORS, verbose=False)
        rows = results_to_rows(results, param=param, model=MODEL)
        df = pd.DataFrame(rows)
        path = os.path.join(out_dir, f"{param}_posterior_contrasts.csv")
        df.to_csv(path, index=False)
        print(f"Wrote {path} ({len(df)} rows)")
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def export_correlation(idata: az.InferenceData, out_dir: str) -> pd.DataFrame:
    v_map = _delta_short_minus_long(idata, "v")
    a_map = _delta_short_minus_long(idata, "a")
    common = sorted(set(v_map) & set(a_map))
    dv = np.array([v_map[s] for s in common])
    da = np.array([a_map[s] for s in common])

    r_pearson, p_pearson = stats.pearsonr(dv, da)

    summary = pd.DataFrame(
        [
            {
                "model": MODEL,
                "analysis": "delta_v_delta_a_short_minus_long",
                "n_subjects": len(common),
                "pearson_r": float(r_pearson),
                "pearson_p": float(p_pearson),
                "note": (
                    "Exploratory Pearson correlation of posterior-mean individual contrasts "
                    "(Short − Long), averaged over 2×2 (prob × transition) cells."
                ),
            }
        ]
    )
    os.makedirs(out_dir, exist_ok=True)
    summary_path = os.path.join(out_dir, "delta_va_correlation_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"Wrote {summary_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nc", default=DEFAULT_NC, help="Path to winning-model InferenceData (.nc)")
    args = parser.parse_args()

    if not os.path.exists(args.nc):
        raise SystemExit(f"InferenceData not found: {args.nc}")

    idata = load_idata(args.nc)
    export_contrasts(idata, COND_EFFECT_DIR)

    if _has_subject_nodes(idata):
        export_correlation(idata, COND_EFFECT_DIR)
    else:
        print(
            "Skipping individual-level correlation export: no *_subj* nodes in .nc "
            "(use a full InferenceData file with subject-level nodes)."
        )


if __name__ == "__main__":
    main()
