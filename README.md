# Salience_Network_Gates_Adaptive_Control_Data_Code_Figure

Reproducibility materials for analyses from a single neuroimaging and behavior study.
Each subfolder is a self-contained mini-package with its own
`README.md`, dependencies, inputs, and figure reproduction notebooks or scripts.

## Repository map

| Subfolder | Language | Entry point | What it reproduces |
|-----------|----------|-------------|-------------------|
| [`behaviral_SF_probabilities/`](behaviral_SF_probabilities/) | R | `notebooks/behavioral_flexibility_stability_analysis.R` | Repeated-measures ANOVAs (accuracy & RT transition cost) and 2×2 main figure |
| [`hddm_analysis/`](hddm_analysis/) | Python | `notebooks/run_example_pipeline.ipynb` | HDDM model comparison, parameter recovery, condition effects, and manuscript figures |
| [`brain_activation/`](brain_activation/) | Python | `notebooks/run_example_pipeline.ipynb` | Second-level fMRI GLM on first-level contrast maps and whole-brain architecture figure |
| [`adaptive_reserve_moderate/`](adaptive_reserve_moderate/) | Python | `notebooks/run_example_pipeline.ipynb` | Adaptive-reserve moderated regression and multi-panel figure |
| [`gradient_dispersion_mediate_moderate/`](gradient_dispersion_mediate_moderate/) | Python | `notebooks/run_example_pipeline.ipynb` | Macro-scale gradient dispersion, moderated mediation, main figure, and split-half supplement |
| [`mediate_moderate_lesion/`](mediate_moderate_lesion/) | Python | `notebooks/run_example_pipeline.ipynb` | Salience-network topology moderated mediation, main figure, and split-half supplement |
| [`gradual_virtual_lesion/`](gradual_virtual_lesion/) | Python | `notebooks/gradual_lesion_figure.ipynb` | Gradual salience-network virtual-lesion moderation and composite figure |

Nested neuroimaging pipelines also provide `run_example_pipeline.ipynb`:

| Path | Purpose |
|------|---------|
| `adaptive_reserve_moderate/graph_theory/notebooks/` | HMM FC → graph metrics → virtual lesions (example or study data) |
| `gradient_dispersion_mediate_moderate/gradient_analysis/notebooks/` | HMM FC → weighted-average FC → functional gradients (example or study data) |

## Quick start

1. **Choose one subfolder** from the table above (you do not need to install all
 environments to reproduce a single figure).
2. Read that subfolder’s `README.md` for dependencies.
3. Open and run **`notebooks/run_example_pipeline.ipynb`** (or the nested path above).
 Pipelines use study data when present; otherwise they generate or load `example_data/`.

Python notebooks numbered `01`, `02`, … can also be run **in order** manually from that
subfolder’s notebook directory. Some pipelines (`gradient_dispersion_*`, `mediate_moderate_lesion`)
require running notebooks **in the same Jupyter kernel** when executed step by step.



## License

Code is provided under the MIT License. See [`LICENSE`](LICENSE).

## Citation

Cite the accompanying manuscript. When reproducing results, also record software versions
from each subfolder’s `requirements.txt` (Python) or `results/sessionInfo.txt` (R).
