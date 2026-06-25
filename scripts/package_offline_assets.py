#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path


def add_dir_if_exists(tar: tarfile.TarFile, path: Path, arcname: str) -> bool:
    if not path.exists():
        return False
    tar.add(path, arcname=arcname)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Package offline assets into logical tar.gz bundles.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--asset-root", default="assets")
    parser.add_argument("--bundle-root", default="offline_bundles")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    asset_root = (project_root / args.asset_root).resolve()
    bundle_root = (project_root / args.bundle_root).resolve()

    plans = [
        ("offline_weights.tar.gz", asset_root / "offline_weights"),
        ("offline_inputs.tar.gz", asset_root / "offline_inputs"),
        ("offline_third_party.tar.gz", asset_root / "offline_third_party"),
    ]

    if not args.dry_run:
        bundle_root.mkdir(parents=True, exist_ok=True)

    results = []
    for bundle_name, src in plans:
        bundle_path = bundle_root / bundle_name
        record = {
            "bundle": str(bundle_path),
            "source": str(src),
            "exists": src.exists(),
            "created": False,
        }
        if src.exists() and not args.dry_run:
            with tarfile.open(bundle_path, "w:gz") as tar:
                add_dir_if_exists(tar, src, src.name)
            record["created"] = True
        results.append(record)

    print(json.dumps({"results": results, "dry_run": args.dry_run}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
