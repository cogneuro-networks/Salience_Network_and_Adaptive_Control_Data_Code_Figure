# Supplementary Code — Second-Level fMRI & Figure

Reproducible notebooks for group-level GLM on first-level contrast maps and
manuscript Figure (Panels A/B/C).

## Directory layout

```text
brain_activation/
├── README.md
├── config.yaml # study paths (edit for your derivatives)
├── config.example.yaml # example_data/ paths
├── requirements.txt
├── nilearn_compat.py
├── example_data/
│ ├── generate_example_data.py
│ ├── gray_mask.nii
│ └── first_level/full_factorial/sub-*/patterns/*_beta.nii.gz
├── figures/
├── results/
└── notebooks/
 ├── run_example_pipeline.ipynb
 ├── 01_load_first_level_data.ipynb
 ├── 02_glm_and_contrasts.ipynb
 └── 03_figure_panel_abc.ipynb
```

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook notebooks/run_example_pipeline.ipynb
```

The pipeline uses study paths from `config.yaml` when first-level beta maps exist.
Otherwise it regenerates `example_data/` and temporarily applies `config.example.yaml`.

## Expected inputs (study reproduction)

Paths in `config.yaml` are resolved relative to `brain_activation/`.

Default layout:

```text
BayesianNew/
├── derivatives/first_level/full_factorial/sub-*/patterns/*_beta.nii.gz
└── mask/gray_mask.nii
```

Subject IDs parsed from first-level filenames are remapped to anonymous BIDS labels
(e.g. `sub-001`) before group analysis.

## Run order (manual)

1. `01_load_first_level_data.ipynb`
2. `02_glm_and_contrasts.ipynb`
3. `03_figure_panel_abc.ipynb`

## Statistical choices (match Methods)

| Setting | Value |
|---------|-------|
| Second-level test | OLS on subject beta maps |
| Multiple comparison (Figure) | Bonferroni, α = 0.05 |
| Cluster extent | ≥ 20 voxels |
| Smoothing at second level | None (`smoothing_fwhm=None`) |
| Simple effects | All design columns (t contrasts) |

## Outputs

- **Figures:** `figures/Figure_whole_brain_architecture.[svg|eps]`
- **Unthresholded z-maps:** `results/second_level/{nii_str}/<contrast>_contrast/`
- **Design tables:** `results/artifacts/design_*.csv`
- **Joblib cache:** `results/cachedir/` (runtime; gitignored)


## Citation

If you use this code, cite the accompanying manuscript and list software
versions recorded in `requirements.txt`.

## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
