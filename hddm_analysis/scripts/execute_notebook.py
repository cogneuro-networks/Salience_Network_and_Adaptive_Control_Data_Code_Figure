"""Execute a notebook in an isolated process (avoids nested-Jupyter ZMQ timeouts)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("notebook", type=Path)
    p.add_argument("--kernel", default=os.environ.get("HDDM_NOTEBOOK_KERNEL", "hddm"))
    p.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("HDDM_PIPELINE_TIMEOUT", "3600")),
    )
    args = p.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("HDDM_PIPELINE_NONINTERACTIVE", "1")

    import nbformat
    from nbclient import NotebookClient

    nb_path = args.notebook.resolve()
    with open(nb_path, encoding="utf-8") as f:
        nb = nbformat.read(f, as_version=4)

    # Drop prior outputs (also removes invalid stream outputs missing "name").
    for cell in nb.cells:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    client = NotebookClient(
        nb,
        timeout=args.timeout,
        kernel_name=args.kernel,
        resources={"metadata": {"path": str(nb_path.parent)}},
    )
    client.execute()
    with open(nb_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
