#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare object C image-to-3D input layout.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    asset_root = Path(args.asset_root)
    output_root = Path(args.output_root)
    src_root = asset_root / "offline_inputs" / "object_c"
    raw_image = src_root / "object_c_raw.png"
    rgba_image = src_root / "object_c_rgba.png"
    dst_root = output_root / "object_c" / "inputs"

    payload = {
        "raw_image": str(raw_image),
        "rgba_image": str(rgba_image),
        "target_root": str(dst_root),
        "dry_run": args.dry_run,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if args.dry_run:
        return

    dst_root.mkdir(parents=True, exist_ok=True)
    if raw_image.exists():
        shutil.copy2(raw_image, dst_root / raw_image.name)
    if rgba_image.exists():
        shutil.copy2(rgba_image, dst_root / rgba_image.name)


if __name__ == "__main__":
    main()
