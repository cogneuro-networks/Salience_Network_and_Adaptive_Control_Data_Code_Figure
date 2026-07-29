# Data dictionary

## `trials.tsv`

Trial-level behavioral data (one row per experimental observation after preprocessing).

| Column | Type | Description |
|--------|------|-------------|
| `subject` | character | Anonymous participant ID (e.g. `sub-001`) |
| `trial` | integer | Trial index within session |
| `transition` | character | Cognitive domain: `flexibility` (task switching) or `stability` (distractor inhibition) |
| `long_short` | character | Perturbation block length: `Long` (low flux) or `Short` (high flux) |
| `prob` | character | Predictability: `prob_diff` (high predictability) or `prob_same` (low predictability) |
| `acc` | integer | Accuracy on switch task target (0/1) |
| `rt` | numeric | Reaction time on switch task target (ms) |
| `base_rt` | numeric | Reaction time on preceding baseline task target (ms) |
| `base_acc` | integer | Accuracy on preceding baseline task target (0/1) |

### Factor coding in analysis script

| Variable | Display label |
|----------|-----------------|
| `transition = flexibility` | Task Switching |
| `transition = stability` | Distractor Inhibition |
| `long_short = Long` | Low Flux |
| `long_short = Short` | High Flux |
| `prob = prob_diff` | High Predictability |
| `prob = prob_same` | Low Predictability |

## RT transition cost (`rt_diff`)

Computed in the analysis script (not stored in the shared trial file):

- Within each participant, `rt_diff = rt - lag(base_rt)` when the previous and current trials are both correct and both RTs exceed 150 ms.
- Only the first row of each `trial` block is retained.
- Baseline probability blocks are excluded.
