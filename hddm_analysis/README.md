# Flexibility–Stability HDDM Analysis

Behavioral data, analysis notebooks, and precomputed model-comparison tables for reproducing manuscript figures and statistics.

## Repository layout

```
hddm_analysis/
├── README.md
├── requirements.txt
├── data/
│ ├── trials_hddm_ready.tsv
│ ├── dataset_meta.json
│ └── DATA_DICTIONARY.md
├── example_data/
│ └── generate_example_data.py # model-comparison CSVs for notebook 02
├── models/transition_prob_duration_10000samples/
├── notebooks/
│ ├── run_example_pipeline.ipynb
│ ├── 01_model_estimation.ipynb
│ ├── 02_model_comparison.ipynb
│ ├── 03_parameter_recovery.ipynb
│ ├── 04_condition_effect_analysis.ipynb
│ └── 05_figures.ipynb
├── results/
│ ├── condition_effects/
│ └── parameter_recovery/
└── figures/
```

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

The pipeline runs notebooks **02–05** using `data/trials_hddm_ready.tsv`. If
`models/transition_prob_duration_10000samples/` is missing metrics or the winning-model
`.nc`, it syncs from `example_data/` (including a synthetic `hddm_va_vat_combined.nc`).
Set env `RUN_HDDM_FIT=1` to include notebook **01** (HDDM refitting; hours per model).

See [`notebooks/README.md`](notebooks/README.md) for step-by-step options.

## Notebook pipeline

| Notebook | Purpose | Typical runtime |
|----------|---------|-----------------|
| `01_model_estimation` | Fit one HDDM candidate (default `hddm_va_vat`) + export CSV / local `.nc` | hours / model |
| `02_model_comparison` | DIC, RMSE, R-hat, rank models | minutes |
| `03_parameter_recovery` | Simulate + refit recovery study (`FIGURES_ONLY=True` by default) | minutes / days |
| `04_condition_effect_analysis` | Condition effect decomposition, Δv–Δa correlation summary | minutes |
| `05_figures` | Manuscript Figure 1–4 + combined panel | minutes |

Package paths resolve via `_resolve_hddm_root()` (looks for `data/trials_hddm_ready.tsv`), so figure/model outputs always land under **`hddm_analysis/`**, not the repo root — even if the Jupyter cwd is the workspace root.



## Citation

Cite the accompanying manuscript and this repository DOI once registered (OSF / Zenodo).

## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
