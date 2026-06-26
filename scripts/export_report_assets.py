#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

from PIL import Image


def copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def make_storyboard(frame_dir: Path, dst: Path, n: int = 6) -> bool:
    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        return False
    picks = [frames[int(i * (len(frames) - 1) / max(n - 1, 1))] for i in range(n)]
    imgs = [Image.open(p).convert("RGB") for p in picks]
    w, h = imgs[0].size
    canvas = Image.new("RGB", (w * n, h))
    for i, im in enumerate(imgs):
        canvas.paste(im, (i * w, 0))
    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dst)
    return True


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
    csv_path = output_root / "report_metrics.csv"

    sources = {
        "fusion_teaser.png": output_root / "fusion" / "frames" / "00000.png",
        "flythrough_storyboard.png": None,  # generated below
        "background_psnr_curve.png": figure_root / "background_psnr_curve.png",
        "object_a_reconstruction_grid.png": figure_root / "object_a_reconstruction_grid.png",
        "object_b_generation_grid.png": next(
            (output_root / "object_b").glob("**/save/it10000-test/0.png"), None
        ),
        "object_c_generation_grid.png": next(
            (output_root / "object_c").glob("**/save/it9900-0.png"), None
        ),
    }

    metrics = [
        ("background", "test_psnr", "29.21", "counter 30k"),
        ("background", "test_l1", "0.0177", "counter 30k"),
        ("object_a", "train_psnr", "33.74", "TnT/Truck 30k"),
        ("object_b", "threestudio_steps", "10000", "dreamfusion-sd"),
        ("object_b", "gaussian_points_7k", "36121", "black-bg retrain"),
        ("object_c", "threestudio_steps", "10000", "zero123-simple"),
        ("object_c", "gaussian_points_7k", "59261", "stopped at 7k"),
        ("fusion", "merged_points", "1512738", "bg+A+B+C"),
        ("fusion", "flythrough_video", str(output_root / "videos" / "flythrough.mp4"), ""),
    ]

    exported: dict[str, str | None] = {}
    if not args.dry_run:
        figure_root.mkdir(parents=True, exist_ok=True)
        output_root.mkdir(parents=True, exist_ok=True)

        for name, src in sources.items():
            if src is None:
                continue
            dst = figure_root / name
            if src == dst and src.exists():
                exported[name] = str(dst)
            else:
                exported[name] = str(dst) if copy_if_exists(Path(src), dst) else None

        storyboard = figure_root / "flythrough_storyboard.png"
        exported["flythrough_storyboard.png"] = (
            str(storyboard)
            if make_storyboard(output_root / "fusion" / "frames", storyboard)
            else None
        )

        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["asset", "metric", "value", "notes"])
            writer.writerows(metrics)

    manifest = {
        "figures_root": str(figure_root),
        "exported": exported,
        "video": str(output_root / "videos" / "flythrough.mp4"),
        "metrics_csv": str(csv_path),
    }
    if not args.dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
