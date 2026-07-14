"""Apply multi-chain / parallel sampling support to the installed kabuki package.

HDDM depends on PyMC 2.3 + kabuki 0.6.5. PyMC 2.3 has no ``chains``/``parallel``
API; this script patches ``kabuki.hierarchical.Hierarchical.sample`` so that::

model.sample(10000, burn=2000, chains=4, parallel=True)

runs four independent MCMC chains in separate worker processes (joblib/loky),
using one CPU core per chain.

Run after installing HDDM in your conda env::

python hddm_analysis/scripts/patch_kabuki_multichain.py

The patched source is also vendored at
``.venv-hddm/build-src/kabuki/kabuki-0.6.5/kabuki/hierarchical.py``.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


PATCH_MARKER = "def _sample_one_chain(model_template, sample_args, sample_kwargs, db, dbname):"
DEVIANCE_MERGE_MARKER = "dev_trace._trace[chain_idx]"


def _find_kabuki_hierarchical() -> Path:
    spec = importlib.util.find_spec("kabuki.hierarchical")
    if spec is None or not spec.origin:
        raise RuntimeError("kabuki is not installed in this interpreter")
    return Path(spec.origin)


def _vendor_source() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "vendor" / "kabuki" / "hierarchical.py",
        here.parent.parent
        / ".venv-hddm"
        / "build-src"
        / "kabuki"
        / "kabuki-0.6.5"
        / "kabuki"
        / "hierarchical.py",
    ]
    for path in candidates:
        if path.is_file() and PATCH_MARKER in path.read_text(encoding="utf-8"):
            return path
    raise FileNotFoundError(
        "Patched kabuki/hierarchical.py not found. Copy it from the project build-src tree."
    )


def main() -> int:
    target = _find_kabuki_hierarchical()
    source = _vendor_source()
    text = target.read_text(encoding="utf-8")
    source_text = source.read_text(encoding="utf-8")
    if PATCH_MARKER in text and DEVIANCE_MERGE_MARKER in text and text == source_text:
        print(f"Already patched (up to date): {target}")
        return 0
    backup = target.with_suffix(".py.bak")
    if not backup.exists():
        shutil.copy2(target, backup)
        print(f"Backup written to {backup}")
    shutil.copy2(source, target)
    print(f"Patched {target} from {source}")
    if DEVIANCE_MERGE_MARKER not in source_text:
        print(
            "Warning: vendor source missing deviance merge; DIC may fail after parallel sampling."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
