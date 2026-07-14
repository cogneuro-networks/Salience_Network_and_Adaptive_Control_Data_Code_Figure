# Gradual Virtual Lesion — Supplementary Analysis

Reproduces the gradual SN lesion moderation analysis and composite figure.

## Contents

| Path | Description |
|------|-------------|
| `notebooks/gradual_lesion_figure.ipynb` | Merge inputs, fit moderation models, render figure |
| `data/` | analysis-ready CSV files (anonymous subject IDs `sub-001`–`sub-043`) |
| `results/` | Model summaries written by the notebook |
| `figures/` | Exported figure (`gradual_lesion_moderation_figure`) |

## Requirements

```bash
pip install -r requirements.txt
```

## Quick start

Run the notebook using the bundled data:

```bash
jupyter nbconvert --to notebook --execute notebooks/gradual_lesion_figure.ipynb
```

## Analysis settings

- HMM states: 3–6 (averaged)
- Parcels: 1000
- Lesion intensities: λ = 0.0, 0.1, …, 1.0
- Model: within-λ z-scored OLS, Coupling ~ ΔQ × Reserve


## Outputs

- `figures/gradual_lesion_moderation_figure.{png,pdf,svg,eps}`
- `results/gradual_lesion_model_b_by_lambda.csv`
- `results/gradual_lesion_model_random_by_lambda.csv`
- `results/gradual_lesion_beta_trajectory.csv`
- `results/gradual_lesion_merged_analysis.csv`
- `results/gradual_lesion_merged_null_analysis.csv`

## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
