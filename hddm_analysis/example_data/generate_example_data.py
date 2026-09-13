"""Generate minimal model-comparison CSVs and a synthetic winning-model .nc file."""
from __future__ import annotations

import argparse
import itertools
import shutil
import tempfile
from pathlib import Path

import arviz as az
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
WINNER_NC = "hddm_va_vat_combined.nc"
N_CHAINS = 4
N_DRAWS = 100
N_SUBJECTS = 43
CONDITION_CELLS = [
    ".".join(levels)
    for levels in itertools.product(
        ["Long", "Short"],
        ["prob_same", "prob_diff"],
        ["flexibility", "stability"],
    )
]
# Plausible group-level means (synthetic; loosely aligned with bundled contrast CSVs).
V_CELL_MEAN = {
    "Long.prob_same.flexibility": 2.35,
    "Long.prob_same.stability": 0.45,
    "Long.prob_diff.flexibility": 2.55,
    "Long.prob_diff.stability": 0.65,
    "Short.prob_same.flexibility": 2.10,
    "Short.prob_same.stability": 0.20,
    "Short.prob_diff.flexibility": 2.30,
    "Short.prob_diff.stability": 0.40,
}
A_CELL_MEAN = {
    "Long.prob_same.flexibility": 1.55,
    "Long.prob_same.stability": 4.20,
    "Long.prob_diff.flexibility": 1.45,
    "Long.prob_diff.stability": 4.10,
    "Short.prob_same.flexibility": 1.30,
    "Short.prob_same.stability": 3.95,
    "Short.prob_diff.flexibility": 1.20,
    "Short.prob_diff.stability": 3.85,
}
T_MEAN = 0.28
MODEL_METRICS = [
    # (model_name, dic, fit_offset, max_rhat) — fit_offset only used to synthesize demo LOO/WAIC
    ("hddm_vatz_vatz", 2682.686025, 0.077091, 1.49),
    ("hddm_vat_vatz", 2713.079185, 0.079860, 1.07),
    ("hddm_vat_vat", 2728.934163, 0.082387, 1.32),
    ("hddm_va_vat", 3444.601499, 0.092762, 1.01),
    ("hddm_va_vatz", 3413.573281, 0.096862, 1.01),
    ("hddm_vaz_vatz", 3764.369430, 0.092883, 1.55),
    ("hddm_va_vaz", 3988.039044, 0.096403, 1.04),
    ("hddm_a_vatz", 3730.637343, 0.098707, 1.04),
    ("hddm_v_vtz", 4358.738143, 0.089098, 1.09),
    ("hddm_a_vaz", 4096.910529, 0.097295, 1.03),
    ("hddm_vaz_vaz", 3969.545821, 0.100630, 1.85),
    ("hddm_va_va", 4035.080558, 0.098603, 1.04),
    ("hddm_v_vat", 4040.293913, 0.098196, 1.05),
    ("hddm_v_va", 4295.120526, 0.096994, 1.00),
    ("hddm_a_vat", 3858.804084, 0.104767, 1.02),
    ("hddm_a_va", 4120.532669, 0.098076, 1.01),
    ("hddm_v_vaz", 4277.793144, 0.097918, 1.05),
    ("hddm_v_vatz", 4064.561578, 0.103118, 1.03),
    ("hddm_v_vt", 4700.147847, 0.101875, 1.00),
    ("hddm_a_atz", 8308.978350, 1.232139, 1.02),
    ("hddm_v_vz", 12715.090976, 0.497292, 1.17),
    ("hddm_a_at", 9650.962832, 1.395621, 1.01),
    ("hddm_v_v", 14061.065314, 0.583449, 1.18),
    ("hddm_a_az", 16944.448878, 1.531461, 1.32),
    ("hddm_a_a", 17197.285001, 1.502896, 1.38),
]


def _trace_from_mean(
    mean: float,
    sd: float,
    rng: np.random.Generator,
    *,
    n_chains: int = N_CHAINS,
    n_draws: int = N_DRAWS,
) -> np.ndarray:
    """Draw a small synthetic posterior with near-converged between-chain mixing."""
    chain_offsets = rng.normal(0.0, sd * 0.03, size=n_chains)
    draws = rng.normal(
        mean + chain_offsets[:, None],
        sd,
        size=(n_chains, n_draws),
    )
    return draws.astype(np.float64)


def _build_idata(posterior: dict[str, np.ndarray]):
    coords = {"chain": range(N_CHAINS), "draw": range(N_DRAWS)}
    dims = {name: ["chain", "draw"] for name in posterior}
    try:
        return az.from_dict(
            posterior=posterior,
            coords=coords,
            dims=dims,
        )
    except TypeError:
        return az.from_dict(
            {"posterior": posterior},
            coords=coords,
            dims=dims,
        )


def _save_idata(idata, out_path: Path) -> None:
    if hasattr(az, "to_netcdf"):
        az.to_netcdf(idata, str(out_path))
        return

    with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        idata.to_netcdf(str(tmp_path))
        shutil.copy2(tmp_path, out_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def write_example_idata(out_dir: Path, *, seed: int = 42) -> Path:
    """Write a synthetic hddm_va_vat InferenceData file for notebooks 04–05."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    posterior: dict[str, np.ndarray] = {}

    for cell, mean in V_CELL_MEAN.items():
        posterior[f"v({cell})"] = _trace_from_mean(mean, 0.18, rng)
    for cell, mean in A_CELL_MEAN.items():
        posterior[f"a({cell})"] = _trace_from_mean(mean, 0.22, rng)
    posterior["t"] = _trace_from_mean(T_MEAN, 0.02, rng)

    # Subject-level random effects: v_subj(cell).<id>, a_subj(cell).<id>
    subj_v_offsets = rng.normal(0.0, 0.35, size=N_SUBJECTS)
    subj_a_offsets = rng.normal(-0.25 * subj_v_offsets, 0.20, size=N_SUBJECTS)
    for sid in range(1, N_SUBJECTS + 1):
        for cell, mean in V_CELL_MEAN.items():
            posterior[f"v_subj({cell}).{sid}"] = _trace_from_mean(
                mean + subj_v_offsets[sid - 1], 0.12, rng
            )
        for cell, mean in A_CELL_MEAN.items():
            posterior[f"a_subj({cell}).{sid}"] = _trace_from_mean(
                mean + subj_a_offsets[sid - 1], 0.10, rng
            )

    idata = _build_idata(posterior)
    out_path = out_dir / WINNER_NC
    _save_idata(idata, out_path)
    return out_path


def write_example_data(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for model, dic, fit_offset, rhat in MODEL_METRICS:
        # Demo LOO/WAIC (deviance scale): preserve relative ordering using DIC + a small offset.
        # Re-fit notebook 01 to replace these with true ArviZ LOO/WAIC.
        loo = float(dic) + float(fit_offset) * 50.0
        waic = float(dic) + float(fit_offset) * 40.0
        pd.DataFrame(
            {"model_name": [model], "dic": [dic], "loo": [loo], "waic": [waic]}
        ).to_csv(out_dir / f"{model}_dic_loo_waic.csv", index=False)

    rhat_rows = []
    for model, _, _, rhat in MODEL_METRICS:
        rhat_rows.append(
            {
                "idata_file": f"../models/transition_prob_duration_10000samples/{model}_combined.nc",
                "max_rhat": rhat,
                "cache_version": 3,
            }
        )
    pd.DataFrame(rhat_rows).to_csv(out_dir / "rhat_cache.csv", index=False)


def sync_models(project_root: Path) -> Path:
    model_dir = project_root / "models" / "transition_prob_duration_10000samples"
    model_dir.mkdir(parents=True, exist_ok=True)
    for src in ROOT.glob("*_dic_loo_waic.csv"):
        shutil.copy2(src, model_dir / src.name)
    shutil.copy2(ROOT / "rhat_cache.csv", model_dir / "rhat_cache.csv")
    nc_src = ROOT / WINNER_NC
    if nc_src.is_file():
        shutil.copy2(nc_src, model_dir / WINNER_NC)
    return model_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sync-models",
        action="store_true",
        help="Copy generated CSVs into hddm_analysis/models/transition_prob_duration_10000samples/",
    )
    args = parser.parse_args()
    write_example_data(ROOT)
    nc_path = write_example_idata(ROOT)
    print(f"Wrote example model metrics to {ROOT}")
    print(f"Wrote synthetic InferenceData: {nc_path}")
    if args.sync_models:
        target = sync_models(ROOT.parent)
        print(f"Synced model metrics to {target}")


if __name__ == "__main__":
    main()
