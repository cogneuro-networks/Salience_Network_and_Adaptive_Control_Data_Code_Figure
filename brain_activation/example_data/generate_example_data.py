"""Generate minimal first-level beta maps and mask for the example pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

import nibabel as nib
import numpy as np

ROOT = Path(__file__).resolve().parent
SHAPE = (24, 24, 24)
SUBJECTS = ["001", "002", "003"]
CONDITIONS = [
    ("Long", "diff", "flexibility"),
    ("Long", "diff", "stability"),
    ("Long", "same", "flexibility"),
    ("Long", "same", "stability"),
    ("Short", "diff", "flexibility"),
    ("Short", "diff", "stability"),
    ("Short", "same", "flexibility"),
    ("Short", "same", "stability"),
]
RNG = np.random.default_rng(42)


def _affine() -> np.ndarray:
    return np.diag([2.0, 2.0, 2.0, 1.0])


def write_example_data(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    mask_data = np.zeros(SHAPE, dtype=np.float32)
    mask_data[4:-4, 4:-4, 4:-4] = 1.0
    mask_path = out_dir / "gray_mask.nii"
    nib.save(nib.Nifti1Image(mask_data, _affine()), mask_path)

    first_level = out_dir / "first_level" / "full_factorial"
    for sub in SUBJECTS:
        pattern_dir = first_level / f"sub-{sub}" / "patterns"
        pattern_dir.mkdir(parents=True, exist_ok=True)
        for idx, (long_short, probability, transition) in enumerate(CONDITIONS):
            beta = RNG.normal(loc=idx * 0.05, scale=0.2, size=SHAPE).astype(np.float32)
            beta *= mask_data
            fname = f"run_{sub}_{long_short}_x_{probability}_{transition}_beta.nii.gz"
            nib.save(nib.Nifti1Image(beta, _affine()), pattern_dir / fname)

    print(f"Wrote mask to {mask_path}")
    print(f"Wrote {len(SUBJECTS) * len(CONDITIONS)} beta maps under {first_level}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT,
        help="Output directory (default: example_data/)",
    )
    args = parser.parse_args()
    write_example_data(args.out_dir.resolve())


if __name__ == "__main__":
    main()
