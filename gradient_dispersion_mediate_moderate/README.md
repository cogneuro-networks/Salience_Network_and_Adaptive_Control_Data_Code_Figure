# Macro-Scale Gradients and Topographic Fidelity — Gradient Dispersion Mediate Moderate

Analysis tables and figure reproduction code for HMM states 3–6 (Schaefer-1000 parcels).

## Layout

```
gradient_dispersion_mediate_moderate/
├── README.md
├── requirements.txt
├── data/
│ ├── analysis_ready.csv
│ ├── panel_a_g12_parcels.csv
│ └── DATA_DICTIONARY.md
├── gradient_analysis/ # HMM FC → gradients pipeline
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

For the neuroimaging gradient pipeline, see
[`gradient_analysis/notebooks/run_example_pipeline.ipynb`](gradient_analysis/notebooks/run_example_pipeline.ipynb).

Figures export to `../figures/` as **PDF, PNG, SVG, and EPS**.
Supplement tables export to `../results/split_half/`.


## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
