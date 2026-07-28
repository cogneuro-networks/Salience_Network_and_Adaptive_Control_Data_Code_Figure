# Brain-State HMM Training — Supplementary Code

Jupyter notebooks for fitting a Gaussian **GLHMM** (Gaussian Linear Hidden
Markov Model) to concatenated Schaefer parcel BOLD time series.

Downstream graph analyses live in `../graph_theory/`.

## Overview

| Notebook | Purpose |
|----------|---------|
| `01_config_and_data_loading.ipynb` | Load configuration and parcel time series |
| `02_train_hmm.ipynb` | Fit GLHMM, save model pickle and training metadata |
| `run_example_pipeline.ipynb` | Run 01→02 with `config.example.yaml` |

Run notebooks **in numerical order**.

## Layout

```
brain_states/
├── config.yaml
├── config.example.yaml
├── data/                 # study inputs (not included in repo)
├── example_data/
├── notebooks/
│   ├── 01_config_and_data_loading.ipynb
│   ├── 02_train_hmm.ipynb
│   └── run_example_pipeline.ipynb
├── hmm_models/           # formal fitted models (gitignored)
└── results/
```

## Requirements

```bash
pip install -r requirements.txt
```

`requirements.txt` installs **glhmm** from PyPI. Pin or replace with the
repository/version cited in the manuscript Data Availability statement if needed.

## Quick start (example pipeline)

The `example_data/` folder contains **anonymized, minimal inputs** intended only
to confirm that dependencies are installed and the pipeline runs end-to-end.
**Do not use these outputs for scientific inference.**

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

Or run notebooks `01`–`02` manually with `BRAIN_STATES_CONFIG=config.example.yaml`.

Example outputs are written to `results/example/`.

## Example inputs (`example_data/`)

| File | Description |
|------|-------------|
| `parcel_timeseries.csv` | Concatenated parcel BOLD (3 subjects × 120 TRs × 18 ROIs) |
| `subject_indices.csv` | Per-subject row ranges in `parcel_timeseries.csv` |

## Configuration

| File | Purpose |
|------|---------|
| `config.example.yaml` | Example pipeline (`example_data/`) |
| `config.yaml` | Formal analysis with study data |

Notebooks load `config.yaml` by default. For example mode, set
`BRAIN_STATES_CONFIG=config.example.yaml` or change `CONFIG_NAME` in notebook `01`.

## Full analysis (study data)

1. Edit `config.yaml` (`K`, `method`, `n_parcels`, `n_subjects`, `n_timepoints`).
2. Place inputs under `data/` (see table below).
3. Run notebooks with the default config (or `BRAIN_STATES_CONFIG=config.yaml`).

### Expected inputs (not included in this repository)

| File | Description |
|------|-------------|
| `data/all_schaefer_parcel{n_parcels}_{method}.csv` | Concatenated parcel time series `(T × P)` |
| `data/all_schaefer_indices_parcel{n_parcels}_{method}.csv` | Subject segment indices `(N × 2)` start/end rows |


### Model output

| File | Description |
|------|-------------|
| `hmm_models/trained_hmm_{n_parcels}parcels_{K}states_{method}.pkl` | Fitted GLHMM (pickle) |
| `results/training_metadata.json` | Shapes, seed, hyper-parameters, free energy |


## Method notes

- **Observation matrix:** `Y = all_schaefer` with shape `(n_subjects × n_timepoints, n_parcels)`.
- **Indices:** subject-wise `[start, end)` row ranges for concatenated `Y`.
- **Model:** `glhmm.glhmm(model_beta=…, K=…, covtype=…, model_mean=…)`.
- **Reproducibility:** `numpy` RNG is seeded via `analysis.random_seed` before `hmm.train`.

## Citation

If you use this code, please cite the accompanying manuscript.

## License

Code in this repository is provided under the MIT License. See [`../../../LICENSE`](../../../LICENSE).
