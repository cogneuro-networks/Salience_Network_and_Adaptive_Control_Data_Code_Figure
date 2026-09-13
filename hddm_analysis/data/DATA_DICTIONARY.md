# Data dictionary

## `trials_hddm_ready.tsv`

trial-level behavioral data for HDDM fitting.

| Column | Type | Description |
|--------|------|-------------|
| `subject` | string | Anonymous participant ID (e.g. `sub-001`) |
| `subj_idx` | int | Integer index used by HDDM (`1` … `N`) |
| `transition` | category | `flexibility` or `stability` block |
| `prob` | category | `prob_same` (50/50) or `prob_diff` (80/20 or 20/80) |
| `long_short` | category | `Long` or `Short` foreperiod |
| `acc` | int | Accuracy (0/1) |
| `rt_ms` | float | Reaction time in milliseconds |

**HDDM preprocessing:** trials with `rt_ms ≤ 150` are excluded before model fitting (anticipatory / invalid responses).

**Not included in this table:** trial index, congruency labels, run-length counters, demographics, E-Prime timestamps, random seeds, session dates, participant names, file paths, and absolute clock times.
