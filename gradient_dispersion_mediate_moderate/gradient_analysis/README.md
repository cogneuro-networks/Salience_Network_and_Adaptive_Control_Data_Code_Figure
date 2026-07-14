# Functional gradient analysis

Subject-specific weighted-average FC (from HMM state-specific FC) → BrainSpace cortical gradients.




## Overview

| Notebook | Purpose |
|----------|---------|
| `01_roi_and_parcel_selection.ipynb` | ROI mask ∩ Schaefer atlas; save `analysis_metadata.json` (≈ `graph_theory` `01`) |
| `02_hmm_decode_and_state_fc.ipynb` | HMM decode + per-subject/state FC (soft γ or hard Viterbi) |
| `03_weighted_average_fc.ipynb` | HMM-occupancy weighted average FC (aligned with `graph_theory` `04`) |
| `04_compute_functional_gradients.ipynb` | BrainSpace gradients on weighted-average FC from `03` |

## Layout

```
gradient_analysis/
├── config.yaml
├── example_data/
├── notebooks/
│ ├── 01_roi_and_parcel_selection.ipynb
│ ├── 02_hmm_decode_and_state_fc.ipynb
│ ├── 03_weighted_average_fc.ipynb
│ ├── 04_compute_functional_gradients.ipynb
│ └── run_example_pipeline.ipynb
└── results/
```

## Example inputs (`example_data/`)

Anonymous, statistically synthetic files that verify the pipeline format. They are **not** study data.

| File | Used by | Description |
|------|---------|-------------|
| `network_labels.csv` | 01 | Parcel → Yeo-7 network labels (18 ROIs, 3 networks) |
| `parcel_timeseries.csv` | 02 | Concatenated parcel BOLD time series (3 subjects × 120 TRs) |
| `subject_indices.csv` | 01, 02 | Row ranges in `parcel_timeseries.csv` |
| `hmm_decode.npz` | 02 | Precomputed HMM posteriors (`Gamma`) and Viterbi path (`vpath`) |

Shared with the companion `graph_theory` project. Regenerate from `graph_theory/example_data/generate_example_data.py --sync-gradient example_data/`.


## Quick start

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

Or run notebooks `01`–`04` manually in order (with `data_mode: example` in `config.yaml`).

Notebook `03` matches the companion `graph_theory` notebook `04_weighted_average_fc.ipynb` (HMM-occupancy weighted FC, no behavioral data).

## Notebook 04 outputs

`04_compute_functional_gradients.ipynb` writes to `results/<mode>/04_gradients/`:

| File | Description |
|------|-------------|
| `weighted_average_gradient_metrics_*_{approach}.csv` | Per-subject gradient metrics: global and network **range**, **dispersion**, mean G1 score, and pairwise **hierarchy_span** |
| `weighted_average_gradient1_gradient2_parcels_*_{approach}.csv` | Group-median G1/G2 parcel embedding (Figure 5 Panel A) |

Range is max − min of the primary gradient (G1); dispersion is the standard deviation of G1 scores.

## Study reproduction

Set `data_mode: study` in `config.yaml` and provide neuroimaging files under `data/` (see notebook headers).

## License

Code in this repository is provided under the MIT License. See [`../../../LICENSE`](../../../LICENSE).
