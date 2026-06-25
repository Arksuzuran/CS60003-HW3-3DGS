#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export report-ready figures and tables manifest.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    output_root = Path(args.output_root)
    figure_root = project_root / "neurips_template" / "figures"

    manifest_path = output_root / "report_assets_manifest.json"
    csv_path = output_root / "report_metrics_template.csv"

    manifest = {
        "figures_root": str(figure_root),
        "expected_assets": [
            "background_psnr_curve.png",
            "object_a_reconstruction_grid.png",
            "object_b_generation_grid.png",
            "object_c_generation_grid.png",
            "fusion_teaser.png",
            "flythrough_storyboard.png",
        ],
        "notes": [
            "Populate these files after training and rendering.",
            "Use this manifest to track report completeness.",
        ],
    }
    if not args.dry_run:
        figure_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["asset", "metric", "value", "notes"])
            writer.writerow(["background", "psnr", "", ""])
            writer.writerow(["background", "ssim", "", ""])
            writer.writerow(["object_a", "train_time_hours", "", ""])
            writer.writerow(["object_b", "train_time_hours", "", ""])
            writer.writerow(["object_c", "train_time_hours", "", ""])

    print(json.dumps({
        "manifest": str(manifest_path),
        "metrics_template": str(csv_path),
        "dry_run": args.dry_run,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
