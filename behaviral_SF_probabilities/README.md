# Behavioral flexibility/stability — analysis and main figure

Supplementary materials for reproducing the repeated-measures ANOVAs and the 2×2 main figure.

## Contents

```
.
├── README.md
├── data/
│ ├── trials.tsv
│ └── data_dictionary.md
├── figures/ # main figure exports
├── results/ # sessionInfo.txt and other non-figure artifacts
└── notebooks/
 └── behavioral_flexibility_stability_analysis.R # ANOVA + main figure
```

## Requirements

- R ≥ 4.2
- CRAN packages: `tidyverse`, `afex`, `effectsize`, `cowplot`, `ggdist`, `this.path`

Install dependencies:

```r
install.packages(c(
 "tidyverse", "afex", "effectsize",
 "cowplot", "ggdist", "this.path"
))
```

Record your session after a successful run (`results/sessionInfo.txt`) when submitting supplementary materials.

## How to run

From R or the terminal in this project directory:

```r
source("notebooks/behavioral_flexibility_stability_analysis.R")
```

Or:

```bash
Rscript notebooks/behavioral_flexibility_stability_analysis.R
```


## Analysis summary

1. **Accuracy:** 3-way repeated-measures ANOVA (`transition × long_short × prob`) via `afex::aov_ez`.
2. **RT transition cost:** difference score `rt_diff` with the rules in `data/data_dictionary.md`; same ANOVA structure.
3. **Figure:** Panel A raincloud + half-density; Panel B accuracy by density; Panels C/D RT spaghetti with 95% ribbons. 

Contrasts for all within-subject factors: sum-to-zero (`contr.sum(2)`).



## License

Code in this repository is provided under the MIT License. See [`../LICENSE`](../LICENSE).
