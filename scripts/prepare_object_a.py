#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare object A COLMAP-ready dataset.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    asset_root = Path(args.asset_root)
    output_root = Path(args.output_root)
    src = asset_root / "offline_inputs" / "object_a"
    dst = output_root / "object_a" / "dataset" / "images"
    colmap_root = output_root / "object_a" / "colmap"

    payload = {
        "source": str(src),
        "target_images": str(dst),
        "colmap_root": str(colmap_root),
        "device": args.device,
        "dry_run": args.dry_run,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.dry_run:
        return

    dst.mkdir(parents=True, exist_ok=True)
    colmap_root.mkdir(parents=True, exist_ok=True)
    for path in src.glob("*"):
        if path.is_file():
            shutil.copy2(path, dst / path.name)

    instructions = colmap_root / "README.txt"
    instructions.write_text(
        "Run COLMAP feature extraction, matching and mapper here, then place sparse/0 under dataset.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
