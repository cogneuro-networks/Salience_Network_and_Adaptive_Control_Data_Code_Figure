# Data dictionary

## `analysis_ready.csv`

Subject-level table merged from gradient metrics, graph metrics, and RT-derived behavioral variables.

| Column | Description |
|--------|-------------|
| `subject` | Anonymous ID (`sub-001` … `sub-043`) |
| `transmodal_distance` | Mean hierarchy span to salience network from transmodal systems |
| `unimodal_distance` | Mean hierarchy span to salience network from unimodal systems |
| `net_SalVentAttn_participation_coefficient_auc` | SN participation coefficient (AUC) |
| `net_SalVentAttn_gradient_dispersion_mean` | SN gradient dispersion |
| `global_modularity_auc` | Global modularity (AUC) |
| `rt_transition_diff__flexibility_stability` | RT difference (flexibility − stability) |
| `rt_duration_diff__long-short` | RT difference (long − short interval) |

Additional upstream metric columns are retained for reproducibility.

## `panel_a_g12_parcels.csv`

Parcel-level G1/G2 coordinates averaged across HMM states 3–6.

| Column | Description |
|--------|-------------|
| `parcel` | Schaefer-1000 parcel index |
| `network` | Yeo-7 network label |
| `g1`, `g2` | Functional gradient coordinates |
| `is_sn` | Salience-network parcel flag |
