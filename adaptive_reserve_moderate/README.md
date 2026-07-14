# Adaptive Reserve Moderation — Supplementary Code

Reproduces the moderated-regression analysis and multi-panel figure for the
adaptive-reserve manuscript section.

## Contents

| Path | Purpose |
|------|---------|
| `notebooks/run_example_pipeline.ipynb` | Run analysis + figure end-to-end |
| `notebooks/01_analysis.ipynb` | Moderated OLS, simple slopes, Johnson–Neyman intervals |
| `notebooks/02_plot.ipynb` | Render figure; export PNG, PDF, SVG, EPS |
| `data/adaptive_reserve_moderation_subject_level.csv` | Subject-level analysis input |
| `graph_theory/` | HMM FC → graph metrics pipeline (see nested README) |
| `figures/` | Saved figure files |
| `results/` | Analysis tables and other non-figure artifacts |

## Setup

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

## Run order (manual)

1. **`01_analysis.ipynb`** — statistical results only.
2. **`02_plot.ipynb`** — figure and exports to `../figures/`.

## Variables

- **X:** `global_modularity_auc`
- **Y:** `rt_transition_diff__flexibility_stability`
- **Moderator (M):** `rt_duration_diff__long-short`
- **HMM states:** 3–6 (aggregated in the subject-level CSV)


## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
