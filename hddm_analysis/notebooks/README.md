# Notebook execution guide

Prefer running from this directory (`hddm_analysis/notebooks/`). Notebooks also locate `hddm_analysis/` by marker file, so outputs stay under this package even if the kernel cwd is elsewhere.

## One-click pipeline

**`run_example_pipeline.ipynb`** — runs notebooks 02–05 (and 01 when `RUN_HDDM_FIT=1`).
Syncs model-comparison CSVs from `../example_data/` when `../models/` is empty.

## Minimal path (figures only)

1. **05_figures.ipynb** — exports Figure 1 + combined panel to `../figures/` (PNG, PDF, EPS, SVG)

For posterior-based panels in **05**, place `hddm_va_vat_combined.nc` under
`../models/transition_prob_duration_10000samples/`. Override with
`WINNER_IDATA_PATH` in cell 1 or env `HDDM_WINNER_IDATA_PATH`. Figure 1 PPC also requires
HDDM (`hddm.generate.gen_rts`).

## Full refitting path

| Step | Notebook | Output |
|------|----------|--------|
| 1 | 01_model_estimation | `../models/.../<model>_combined.nc` |
| 2 | 02_model_comparison | `model_selection.csv`, `model_table`; optional `best_idata` |
| 3 | 03_parameter_recovery | `../results/parameter_recovery/<tag>/` (CSVs) + `../figures/parameter_recovery/<tag>/` (scatter plots) |
| 4 | 04_condition_effect_analysis | condition effect tables, Δv–Δa summary |
| 5 | 05_figures | Figure 1 (PPC) + `Figure_combined_v_a_DDM_2x3` |

## `02_model_comparison.ipynb`

Model comparison: DIC / RT-RMSE ranking, group-level R-hat, and automated winner selection.

**Inputs:**

- `../models/transition_prob_duration_10000samples/*_dic_rmse_percentiles.csv`
- `../models/transition_prob_duration_10000samples/rhat_cache.csv` (group-level max R-hat per model)
- Optional local `*_combined.nc` files

**Outputs:**

- `model_selection.csv` — full comparison table (written under `MODEL_DIR`)
- `model_table` — in-memory DataFrame for downstream notebooks
- `best_idata` — only when `LOAD_BEST_IDATA = True` and a local `.nc` exists

**Configuration flags (cell 2):**

| Flag | Default | Purpose |
|------|---------|---------|
| `LOAD_BEST_IDATA` | `False` | Load winning-model InferenceData; enable locally for notebooks 04–05 |
| `RECOMPUTE_RHAT` | `True` | Recompute R-hat from local `.nc` when present; otherwise use `rhat_cache.csv` |
| `MANUSCRIPT_WINNER` | `"hddm_va_vat"` | Expected winner; notebook warns if automated selection differs |
| `RHAT_THRESHOLD` | `1.01` | Convergence cutoff on group-level max R-hat |

**Selection rules (matches manuscript Methods):**

1. Rank all candidates by DIC and RT-RMSE (lower is better).
2. Compute `combined_rank = 0.5 × rank_dic + 0.5 × rank_rmse`.
3. Exclude models with group-level max R-hat > 1.01 (subject-level `*_subj*` rows are ignored).
4. Select the converged model with the smallest `combined_rank`; tie-break on lower DIC.

## Notes

- **`01`** and **`03`** are computationally expensive (hours to days). Precomputed CSVs in `../models/` and `../results/` are enough for figure reproduction.
- **`01_model_estimation` prerequisites:** Python **3.8**, PyMC **2.3.8**, HDDM **0.9.x** (see `../requirements.txt`). The notebook checks for the kabuki multi-chain patch before sampling.
- **Multi-chain parallel MCMC:** classic HDDM uses PyMC 2.3, which has no built-in `chains`/`parallel` API. After installing HDDM, run once:
 ```bash
 python ../scripts/patch_kabuki_multichain.py
 ```
 Then call `model.sample(..., chains=4, parallel=True)` directly — each chain runs in its own worker **process** (one CPU core per chain). Do **not** use PyMC3 with HDDM.
- **Default model in `01`:** `hddm_va_vat` (manuscript winning model). Set `ACTIVE_MODEL_STEM` to fit other candidates listed in `MODEL_CANDIDATES`.
- InferenceData (`.nc`) files are optional local inputs for posterior traces in **04** and **05**. **02** runs without `.nc` using precomputed CSVs and `rhat_cache.csv`.

## `04_condition_effect_analysis.ipynb`

Condition effect statistics from precomputed CSVs or local InferenceData.

**Precomputed inputs (no `.nc` required):**

- `../results/condition_effects/v_posterior_contrasts.csv`
- `../results/condition_effects/a_posterior_contrasts.csv`
- `../results/condition_effects/delta_va_correlation_summary.csv`

**Configuration flags (cell 2):**

| Flag | Default | Purpose |
|------|---------|---------|
| `RECOMPUTE_FROM_IDATA` | `False` | Recompute from local `.nc` when available |
| `VERBOSE` | `False` | Print per-condition diagnostics during effect decomposition |

Regenerate CSVs locally with: `python ../scripts/export_condition_effect_results.py --nc path/to/hddm_va_vat_combined.nc`
