# Supplementary Code — First-Level fMRI GLM (Full Factorial)

Run-wise first-level GLM for the flexibility-stability task. Fits one regressor per
experimental condition, includes motion and physiological confounds, and writes
condition-specific beta maps for downstream group analysis
([`brain_activation/`](../brain_activation/) second-level pipeline).

Preprocessed BOLD and event files are **not** bundled in this folder; point the notebook
or CLI at your BIDS dataset and fMRIPrep derivatives (see below).

## Directory layout

```text
full_factorial/
├── README.md
├── requirements.txt
├── fmri_first_level.py # core pipeline (CLI + importable module)
├── fmri_first_level.ipynb # notebook entry point with path validation
└── sub-*/ # per-subject outputs (runtime; not bundled)
 ├── betas/ # condition beta and variance maps
 ├── model/ # design matrix TSV
 └── figures/ # design matrix and correlation QC plots
```

## Expected inputs

Default layout (edit paths in the notebook or CLI if your data live elsewhere):

```text
{BIDS_ROOT}/
├── sub-*/func/*_task-flexibilitystability_run-*_events.tsv
└── derivatives/
 └── sub-*/func/
 ├── *_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
 ├── *_space-MNI152NLin2009cAsym_desc-brain_mask.nii.gz
 └── *_desc-confounds_timeseries.tsv
```

Required files per subject and run:

| Input | Description |
|-------|-------------|
| Events TSV | BIDS `*_events.tsv` with `onset`, `duration`, `trial_type`, and `blocks` |
| Preprocessed BOLD | fMRIPrep `*_desc-preproc_bold.nii.gz` in MNI152NLin2009cAsym |
| Brain mask | fMRIPrep `*_desc-brain_mask.nii.gz` |
| Confounds | fMRIPrep `*_desc-confounds_timeseries.tsv` |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter lab fmri_first_level.ipynb
```

Or run from the command line:

```bash
python fmri_first_level.py \
 --bids-root /path/to/BIDS \
 --derivatives-dir /path/to/BIDS/derivatives \
 --output-dir /path/to/full_factorial \
 --n-jobs 4
```

In the notebook, set `BIDS_ROOT`, `DERIVATIVES_DIR`, and `OUTPUT_DIR` in the
configuration cell. Use `TEST_SINGLE_SUBJECT = True` to validate one subject before
batch processing.

## Statistical choices (match Methods)

| Setting | Value |
|---------|-------|
| Design | 2 × 2 × 2 full factorial: `long_short` × `probability` × `trial_type` |
| Extra regressors | `rest_onset` (20 s boxcar), error trials via `acc` (1 s) |
| Confounds | 24-parameter motion, CSF/WM, FD, motion/non-steady outliers (fMRIPrep) |
| HRF | Glover |
| Drift | Cosine high-pass, 0.01 Hz |
| Noise model | AR(1) |
| Event duration | 1.0 s (per condition onset) |
| Smoothing | 6 mm FWHM |
| Slice-time reference | 0.5 |

Condition labels are built from the `blocks` column (`SF8020`/`SF2080` → `prob_diff`,
`SF5050` → `prob_same`; split on `Proce` for `long_short`).

## Outputs

Per subject under `{output_dir}/sub-*/`:

| Path | Description |
|------|-------------|
| `model/*_desc-design_matrix.tsv` | First-level design matrix |
| `figures/*_desc-design_matrix.png` | Design matrix plot |
| `figures/*_desc-design_corr.png` | Regressor correlation plot |
| `betas/{subject}_{condition}_run-{r}_beta.nii.gz` | Condition beta map |
| `betas/{subject}_{condition}_run-{r}_varbeta.nii.gz` | Condition beta variance map |

Downstream second-level group GLM and figure code live in
[`../brain_activation/`](../brain_activation/); point that package's `config.yaml`
at your first-level derivatives.


## Citation

If you use this code, cite the accompanying manuscript and list software versions
recorded in `requirements.txt`.

## License

Code in this repository is provided under the MIT License. See [`../../LICENSE`](../../LICENSE).
