"""Generate anonymized example inputs for the example pipeline only."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)

K = 3
N_SUBJECTS = 3
N_TIMEPOINTS = 120
N_ROIS = 18
SUBJECTS = ["sub-01", "sub-02", "sub-03"]
NETWORKS = (["Vis"] * 6) + (["SomMot"] * 6) + (["SalVentAttn"] * 6)

OUTPUT_FILES = (
    "parcel_timeseries.csv",
    "subject_indices.csv",
    "network_labels.csv",
    "hmm_decode.npz",
)

LEGACY_FILES = (
    "example_metadata.json",
    "all_schaefer_parcel1000_example.csv",
    "all_schaefer_indices_parcel1000_example.csv",
    "per_subject_state_FC.npz",
    "per_subject_state_FC_summary.csv",
    "weighted_average_FC.npz",
)


def write_example_data(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_total = N_SUBJECTS * N_TIMEPOINTS

    base = RNG.normal(0, 0.4, size=(n_total, N_ROIS))
    for s in range(N_SUBJECTS):
        start = s * N_TIMEPOINTS
        end = start + N_TIMEPOINTS
        drift = np.sin(np.linspace(0, 4 * np.pi, N_TIMEPOINTS))[:, None]
        base[start:end] += 0.15 * drift
        base[start:end, :6] += 0.1 * RNG.normal(size=(N_TIMEPOINTS, 1))
        base[start:end, 6:12] += 0.1 * RNG.normal(size=(N_TIMEPOINTS, 1))
        base[start:end, 12:] += 0.1 * RNG.normal(size=(N_TIMEPOINTS, 1))

    pd.DataFrame(base).to_csv(out_dir / "parcel_timeseries.csv", index=False)

    subject_rows = []
    for i, subj in enumerate(SUBJECTS):
        start = i * N_TIMEPOINTS
        end = start + N_TIMEPOINTS
        subject_rows.append(
            {
                "subject": subj,
                "start_row": start,
                "end_row": end,
                "n_timepoints": N_TIMEPOINTS,
            }
        )
    pd.DataFrame(subject_rows).to_csv(out_dir / "subject_indices.csv", index=False)

    pd.DataFrame(
        {"parcel_index": np.arange(N_ROIS), "network": NETWORKS}
    ).to_csv(out_dir / "network_labels.csv", index=False)

    gamma = RNG.dirichlet([1.2, 1.0, 0.8], size=n_total)
    vpath = np.zeros((n_total, K))
    vpath[np.arange(n_total), np.argmax(gamma, axis=1)] = 1.0
    np.savez_compressed(
        out_dir / "hmm_decode.npz",
        Gamma=gamma.astype(np.float32),
        vpath=vpath.astype(np.float32),
    )

    for legacy in LEGACY_FILES:
        legacy_path = out_dir / legacy
        if legacy_path.exists():
            legacy_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate shared example_data inputs.")
    parser.add_argument(
        "--sync-gradient",
        type=Path,
        default=None,
        help="Optional path to gradient_analysis/example_data to mirror the same files.",
    )
    args = parser.parse_args()

    write_example_data(ROOT)
    print(f"Wrote example data to {ROOT}")

    if args.sync_gradient is not None:
        args.sync_gradient.mkdir(parents=True, exist_ok=True)
        for legacy in LEGACY_FILES:
            legacy_path = args.sync_gradient / legacy
            if legacy_path.exists():
                legacy_path.unlink()
        for name in OUTPUT_FILES:
            shutil.copy2(ROOT / name, args.sync_gradient / name)
        print(f"Synced example data to {args.sync_gradient}")


if __name__ == "__main__":
    main()
