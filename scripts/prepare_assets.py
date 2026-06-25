#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_manifest_items(manifest: dict) -> Iterable[dict]:
    for bundle in manifest.get("bundles", {}).values():
        for item in bundle.get("items", []):
            yield item


def load_manifest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import yaml  # type: ignore

        return yaml.safe_load(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate offline asset layout.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--asset-root", default="assets")
    parser.add_argument("--output-root", default="outputs")
    parser.add_argument("--echo-config", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    asset_root = Path(args.asset_root).resolve()
    manifest_path = project_root / "offline_assets_manifest" / "offline_assets.yaml"

    if args.echo_config:
      print(json.dumps({
          "project_root": str(project_root),
          "asset_root": str(asset_root),
          "output_root": str(Path(args.output_root).resolve()),
          "manifest": str(manifest_path),
      }, indent=2, ensure_ascii=False))
      return

    manifest = load_manifest(manifest_path)
    results = []
    missing = []

    for item in iter_manifest_items(manifest):
        rel = item["path"]
        abs_path = project_root / rel
        exists = abs_path.exists()
        record = {
            "id": item["id"],
            "path": str(abs_path),
            "exists": exists,
            "purpose": item.get("purpose", ""),
        }
        if exists and abs_path.is_file():
            record["sha256_actual"] = sha256_file(abs_path)
        elif not exists:
            missing.append(item["id"])
        results.append(record)

    print(json.dumps({"results": results, "missing": missing}, indent=2, ensure_ascii=False))

    if missing:
        raise SystemExit(f"Missing offline assets: {', '.join(missing)}")


if __name__ == "__main__":
    main()
