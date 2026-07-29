# Salience Network Topology and Moderated Mediation — Supplementary Code

Reproduces the multi-panel figure linking salience-network participation, global modularity,
adaptive reserve, and behavioral coordination (HMM states 3–6; 1000 parcels), plus
split-half validation of the moderated mediation model (Hayes Model 14).

## Layout

```
mediate_moderate_lesion/
├── README.md
├── requirements.txt
├── data/
│ └── analysis_input.csv
├── notebooks/
│ ├── run_example_pipeline.ipynb
│ ├── 01_statistics.ipynb
│ ├── 02_panel_plotting.ipynb
│ ├── 03_main_figure.ipynb
│ └── 04_split_half_supplement.ipynb
├── figures/
└── results/
 └── split_half/
```

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

Or run `01_statistics` → `02_panel_plotting` → `03_main_figure` manually in the **same kernel**.
Optionally run `04_split_half_supplement.ipynb` (~5–15 min with 1,000 repeated splits).

Figures export to `../figures/` as **PDF, PNG, SVG, and EPS**.
Supplement tables export to `../results/split_half/`.

## Expected inputs

### `analysis_input.csv` (required)

Subject-level table. Must include at least:

| Column | Description |
|--------|-------------|
| `subject` | Anonymous ID (e.g. `sub-001`) |
| `global_modularity_auc` | Intact global modularity (AUC) |
| `lesion_net_{Network}_global_modularity_auc` | Lesioned modularity per network |
| `net_{Network}_participation_coefficient_auc` | Network participation coefficient (AUC) |
| `rt_duration_diff__long-short` | Adaptive reserve (RT duration difference) |
| `rt_transition_diff__flexibility_stability` | Behavioral coordination (RT transition difference) |

`{Network}` ∈ `Cont`, `Default`, `DorsAttn`, `SalVentAttn`, `SomMot`, `Vis`.

### Optional FC display files

- `fc_display_matrices.npz` — group-level intact/lesioned FC for panel-b heatmaps
- `per_subject_fc.npz` — per-subject FC fallback for heatmaps

When no FC file is found, panel-b heatmaps use schematic block-structured matrices.

## Outputs

| File | Description |
| ---- | ----------- |
| `figures/salience_topology_mediation.{pdf,png,svg,eps}` | Main multi-panel figure |
| `figures/supp_mediation_split_half.{pdf,png,svg,eps}` | Split-half supplement figure |
| `results/split_half/mediation_split_half_*.csv` | Supplement tables |

## Reproducibility

- Random seed for the illustrative split-half: `42`
- Bootstrap resamples (single split): `5000`
- Repeated W-stratified splits: `1000` (set `N_REPEATED=100` in notebook `04` for a faster dry run)
- Z-scores in split-half analyses use full-sample mean and SD

## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
