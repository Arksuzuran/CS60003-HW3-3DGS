#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan B/C conversion into gaussian-compatible datasets.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    plan = {
        "object_b_mesh_root": str(output_root / "object_b"),
        "object_c_mesh_root": str(output_root / "object_c"),
        "synthetic_dataset_targets": [
            str(output_root / "object_b_gaussian_dataset"),
            str(output_root / "object_c_gaussian_dataset"),
        ],
        "notes": [
            "Render multi-view images around the generated asset.",
            "Export camera transforms in NeRF-Synthetic-like format.",
            "Train gaussian-splatting separately on each synthetic dataset.",
        ],
        "dry_run": args.dry_run,
    }
    print(json.dumps(plan, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
