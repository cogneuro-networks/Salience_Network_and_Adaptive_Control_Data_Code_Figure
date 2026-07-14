# Graph Theory Analysis — Supplementary Code

Jupyter notebooks for computing **modularity** and **participation coefficient** on subject-specific functional connectivity (FC), including intact-state and virtual-lesion analyses.

## Overview

| Notebook | Purpose |
|----------|---------|
| `01_config_and_data_loading.ipynb` | Load configuration, HMM model, parcel time series, ROI mask |
| `02_hmm_decode_and_state_fc.ipynb` | HMM decoding and per-subject/state FC extraction |
| `03_graph_metrics_functions.ipynb` | Community detection and graph metric functions |
| `04_weighted_average_fc.ipynb` | HMM occupancy–weighted average FC per subject |
| `05_intact_graph_analysis.ipynb` | Intact metrics + binary network virtual lesions |
| `06_gradual_lesion_analysis.ipynb` | Gradual network lesions (λ = 0.1–1.0) and random null controls |

Run notebooks **in numerical order**. Each notebook saves intermediate outputs under `results/` for the next step.

## Layout

```
graph_theory/
├── config.yaml
├── config.example.yaml
├── data/ # study inputs (not included in repo)
├── example_data/
│ └── generate_example_data.py
├── notebooks/
│ ├── 01_config_and_data_loading.ipynb
│ ├── …
│ └── run_example_pipeline.ipynb
└── results/
```

## Requirements

```bash
pip install -r requirements.txt
```

Install **glhmm** from the repository/version cited in the manuscript Data Availability statement (not required for the example pipeline; see below).

## Quick start (example pipeline)

The `example_data/` folder contains **anonymized, minimal inputs** intended only to confirm that dependencies are installed and the pipeline runs end-to-end. **Do not use these outputs for scientific inference.**

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

Or run notebooks `01`–`06` manually in order (with `GRAPH_THEORY_CONFIG=config.example.yaml`).

Example outputs are written to `results/example/`.

## Example inputs (`example_data/`)

| File | Used by | Description |
|------|---------|-------------|
| `network_labels.csv` | 01 | Parcel → Yeo-7 network labels (18 ROIs, 3 networks) |
| `parcel_timeseries.csv` | 01, 02 | Concatenated parcel BOLD time series (3 subjects × 120 TRs) |
| `subject_indices.csv` | 01 | Row ranges in `parcel_timeseries.csv` |
| `hmm_decode.npz` | 02 | Precomputed HMM posteriors (`Gamma`) and Viterbi path (`vpath`) |

Regenerate (and optionally sync to `gradient_analysis/example_data/`):

```bash
python example_data/generate_example_data.py --sync-gradient ../gradient_dispersion_mediate_moderate/gradient_analysis/example_data
```

## Configuration

Two config files are provided:

| File | Purpose |
|------|---------|
| `config.example.yaml` | Example pipeline (`example_data/`) |
| `config.yaml` | Formal analysis with study data |

Notebooks load `config.yaml` by default. For example mode, set `GRAPH_THEORY_CONFIG=config.example.yaml` or change `CONFIG_NAME` in notebook `01`.

## Full analysis (study data)

Edit `config.yaml` and place neuroimaging files under `data/`. Run notebooks with the default config (or `GRAPH_THEORY_CONFIG=config.yaml`).

### Expected inputs (not included in this repository)

| File | Description |
|------|-------------|
| `data/all_schaefer_parcel1000_{method}.csv` | Concatenated parcel time series |
| `data/all_schaefer_indices_parcel1000_{method}.csv` | Subject/time indices |
| `hmm_models/trained_hmm_1000parcels_{K}states_{method}.pkl` | Fitted HMM |
| `mask/merged_all_statistical_masks.nii.gz` | Study ROI mask |
| Schaefer2018 atlas | Downloaded via nilearn if not cached |

Access to raw neuroimaging data is governed by the ethics approval and data-sharing policy stated in the manuscript.

## Metrics

- **Modularity** — Louvain community detection with consensus clustering (`consensus_runs` repetitions, edge retention threshold `consensus_threshold`)
- **Participation coefficient** — mean node-level participation coefficient on the thresholded graph

Graphs are binarized by retaining the top `threshold` fraction of positive pairwise connections.

## Virtual lesions

1. **Intact + binary network lesion** (`05`): for each Yeo–Schaefer network, zero all connections of ROIs in that network, then recompute global metrics.
2. **Gradual network lesion** (`06`): disconnect `round(λ × k)` ROIs in a target network (λ = 0.1, 0.2, …, 1.0).
3. **Random null lesion** (`06`): matched-size random ROI sets outside the target network.

## Outputs

Results are written to `results/` as CSV files. Example runs go to `results/example/`; study runs use `results/` (see `config.yaml`). Filenames include parcel count, HMM state count, and analysis method from the active config.

## Citation

If you use this code, please cite the accompanying manuscript.

## License

Code in this repository is provided under the MIT License. See [`../../../LICENSE`](../../../LICENSE).
