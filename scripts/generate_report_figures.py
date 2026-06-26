#!/usr/bin/env python3
"""Generate Loss / PSNR curves and a reconstruction comparison figure for the
experiment report from existing training logs and threestudio CSV metrics.

Run with any python that has matplotlib + pandas + Pillow::

    python scripts/generate_report_figures.py \
        --project-root "$PWD" --out report/figures
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def parse_3dgs_log(log_path: Path):
    """Parse gaussian-splatting train.log for per-iter loss and eval metrics."""
    if not log_path.exists():
        return [], {}, []
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    iters, losses = [], []
    for m in re.finditer(r"(\d+)/\d+.*?Loss=([0-9.eE+-]+)", text):
        it, lo = int(m.group(1)), float(m.group(2))
        if it > 0 and (not iters or it > iters[-1]):
            iters.append(it)
            losses.append(lo)
    evals = {}
    for m in re.finditer(r"\[ITER (\d+)\] Evaluating (\w+): L1 ([0-9.eE+-]+) PSNR ([0-9.eE+-]+)", text):
        it, split, l1, psnr = int(m.group(1)), m.group(2), float(m.group(3)), float(m.group(4))
        evals.setdefault(it, {})[split] = (l1, psnr)
    return iters, losses, evals


def plot_3dgs_curve(iters, losses, evals, title, out_path: Path):
    fig, ax1 = plt.subplots(figsize=(6, 3.2))
    ax1.plot(iters, losses, color="#2b6cb0", linewidth=0.8, label="Training loss")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Loss", color="#2b6cb0")
    ax1.tick_params(axis="y", labelcolor="#2b6cb0")
    ax1.set_title(title)
    ax1.set_yscale("log")
    if evals:
        ax2 = ax1.twinx()
        ax2.set_ylabel("PSNR (dB)", color="#c53030")
        ax2.tick_params(axis="y", labelcolor="#c53030")
        for it, splits in evals.items():
            for split, (l1, psnr) in splits.items():
                mk = "o" if split == "test" else "s"
                ax2.scatter([it], [psnr], color="#c53030", marker=mk, s=28,
                            edgecolors="black", linewidths=0.4,
                            label=f"{split} PSNR" if it == min(evals) else None)
        ax2.legend(loc="lower right", fontsize=8)
    ax1.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  -> {out_path}")


def plot_threestudio_csv(csv_path: Path, loss_cols, title, out_path: Path):
    if not csv_path.exists():
        print(f"  [skip] {csv_path} missing")
        return
    rows = []
    with csv_path.open() as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                step = int(float(r["step"]))
                row = {"step": step}
                for c in loss_cols:
                    if c in r and r[c] not in ("", None):
                        row[c] = float(r[c])
                rows.append(row)
            except (ValueError, KeyError):
                continue
    if not rows:
        print(f"  [skip] no rows in {csv_path}")
        return
    steps = [r["step"] for r in rows]
    fig, ax = plt.subplots(figsize=(6, 3.2))
    for c in loss_cols:
        ys = [r.get(c, None) for r in rows]
        xs = [s for s, y in zip(steps, ys) if y is not None]
        ys2 = [y for y in ys if y is not None]
        if xs:
            ax.plot(xs, ys2, linewidth=0.8, label=c.replace("train/loss_", "").replace("train/", "").replace("trian/", ""))
    ax.set_xlabel("Step")
    ax.set_ylabel("Loss")
    ax.set_title(title)
    ax.set_yscale("symlog")
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  -> {out_path}")


def make_objA_compare(input_dir: Path, n: int, out_path: Path):
    imgs = sorted(input_dir.glob("*.png"))
    if not imgs:
        print("  [skip] no objA input images")
        return
    picks = [imgs[int(i * (len(imgs) - 1) / max(n - 1, 1))] for i in range(n)]
    ims = [Image.open(p).convert("RGB") for p in picks]
    w = max(im.width for im in ims)
    h = max(im.height for im in ims)
    target_h = 200
    scale = target_h / h
    tw, th = int(w * scale), target_h
    canvas = Image.new("RGB", (tw * n, th), "white")
    for i, im in enumerate(ims):
        canvas.paste(im.resize((tw, th)), (i * tw, 0))
    canvas.save(out_path)
    print(f"  -> {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--out", default="report/figures")
    args = parser.parse_args()
    root = Path(args.project_root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print("[1/5] background loss/psnr curve")
    iters, losses, evals = parse_3dgs_log(root / "outputs/bg/counter/train.log")
    plot_3dgs_curve(iters, losses, evals, "Background (counter) 3DGS training",
                    out / "bg_loss_psnr_curve.png")

    print("[2/5] object A loss/psnr curve")
    iters, losses, evals = parse_3dgs_log(root / "outputs/object_a/train.log")
    plot_3dgs_curve(iters, losses, evals, "Object A (Truck) 3DGS training",
                    out / "objA_loss_psnr_curve.png")

    print("[3/5] object B loss curve")
    b_csv = next((root / "outputs/object_b").glob("**/csv_logs/version_0/metrics.csv"), None)
    if b_csv:
        plot_threestudio_csv(b_csv,
                             ["train/loss_sds", "train/loss_orient", "train/loss_sparsity"],
                             "Object B (DreamFusion-SD) training loss",
                             out / "objB_loss_curve.png")

    print("[4/5] object C loss curve")
    c_csv = next((root / "outputs/object_c").glob("**/csv_logs/version_0/metrics.csv"), None)
    if c_csv:
        cols = ["train/loss_sd", "train/loss_sparsity"]
        # normal_smoothness col has typo "trian/" in header
        if c_csv.exists():
            with c_csv.open() as f:
                hdr = f.readline().strip().split(",")
            for h in hdr:
                if "normal_smoothness" in h:
                    cols.append(h)
        plot_threestudio_csv(c_csv, cols,
                             "Object C (Zero123) training loss",
                             out / "objC_loss_curve.png")

    print("[5/5] object A reconstruction grid")
    make_objA_compare(root / "outputs/object_a/colmap_ws/input", 6,
                      out / "objA_recon_compare.png")

    print("\nDone. figures in", out)


if __name__ == "__main__":
    main()
