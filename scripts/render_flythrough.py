#!/usr/bin/env python3
"""Render a cinematic fly-through of a (merged) 3D Gaussian scene.

The merged scene is just a ``point_cloud.ply`` with no associated cameras, so we
synthesise a smooth orbiting camera path. Scene geometry/scale and field of view
are inferred from the background model's ``cameras.json`` (produced during 3DGS
training) so the trajectory stays inside the real captured volume.

Run with the gsbg2 environment python (diff_gaussian_rasterization)::

    python scripts/render_flythrough.py \
        --ply outputs/fusion/merged_gaussians.ply \
        --cameras outputs/bg/counter/cameras.json \
        --out-frames outputs/fusion/frames \
        --out-video outputs/videos/flythrough.mp4
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch


def add_gs_to_path() -> None:
    gs_root = os.environ.get("GAUSSIAN_SPLATTING_ROOT")
    if not gs_root:
        here = Path(__file__).resolve().parent.parent
        gs_root = str(here / "third_party" / "gaussian-splatting")
    if gs_root not in sys.path:
        sys.path.insert(0, gs_root)


def look_at_R_wc(cam_pos: np.ndarray, target: np.ndarray, world_up=(0.0, 1.0, 0.0)) -> np.ndarray:
    """World-to-camera rotation with OpenCV axes (x-right, y-down, z-forward)."""
    f = target - cam_pos
    f = f / (np.linalg.norm(f) + 1e-12)
    up = np.asarray(world_up, dtype=np.float64)
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-6:
        r = np.cross(f, np.array([0.0, 0.0, 1.0]))
    r = r / (np.linalg.norm(r) + 1e-12)
    u = np.cross(r, f)  # camera up
    y_down = -u
    R_wc = np.stack([r, y_down, f], axis=0)  # rows are camera axes in world
    return R_wc.astype(np.float64)


def build_minicam(MiniCam, getWorld2View2, getProjectionMatrix,
                  cam_pos: np.ndarray, target: np.ndarray,
                  fovx: float, fovy: float, width: int, height: int):
    R_wc = look_at_R_wc(cam_pos, target)
    R_cw = R_wc.T  # 3DGS stores c2w rotation; getWorld2View2 transposes it back
    T = -R_wc @ cam_pos
    znear, zfar = 0.01, 100.0
    w2c = torch.tensor(getWorld2View2(R_cw, T)).transpose(0, 1).cuda()
    proj = getProjectionMatrix(znear=znear, zfar=zfar, fovX=fovx, fovY=fovy).transpose(0, 1).cuda()
    full = (w2c.unsqueeze(0).bmm(proj.unsqueeze(0))).squeeze(0)
    return MiniCam(width, height, fovy, fovx, znear, zfar, w2c, full)


def estimate_scene(cameras_json: Path):
    data = json.loads(cameras_json.read_text())
    positions = np.array([c["position"] for c in data], dtype=np.float64)
    center = positions.mean(axis=0)
    radius = float(np.percentile(np.linalg.norm(positions - center, axis=1), 80))
    cam0 = data[0]
    fx, w = cam0["fx"], cam0["width"]
    fy, h = cam0["fy"], cam0["height"]
    fovx = 2 * math.atan(w / (2 * fx))
    fovy = 2 * math.atan(h / (2 * fy))
    mean_height = float(positions[:, 1].mean())
    return center, max(radius, 1e-3), fovx, fovy, mean_height


def main() -> None:
    parser = argparse.ArgumentParser(description="Fly-through renderer for merged 3DGS scene")
    parser.add_argument("--ply", required=True)
    parser.add_argument("--cameras", required=True, help="background cameras.json for scale/fov")
    parser.add_argument("--out-frames", required=True)
    parser.add_argument("--out-video", required=True)
    parser.add_argument("--n-frames", type=int, default=288)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--sh-degree", type=int, default=3)
    parser.add_argument("--radius-scale", type=float, default=0.9)
    parser.add_argument("--turns", type=float, default=2.0)
    parser.add_argument("--white-bg", action="store_true")
    args = parser.parse_args()

    add_gs_to_path()
    from argparse import Namespace

    from gaussian_renderer import render
    from scene.cameras import MiniCam
    from scene.gaussian_model import GaussianModel
    from utils.graphics_utils import getProjectionMatrix, getWorld2View2

    frames_dir = Path(args.out_frames)
    frames_dir.mkdir(parents=True, exist_ok=True)
    Path(args.out_video).parent.mkdir(parents=True, exist_ok=True)

    center, radius, fovx, fovy, mean_h = estimate_scene(Path(args.cameras))
    target = center.copy()
    orbit_r = radius * args.radius_scale
    print(f"scene center={center} radius={radius:.3f} orbit_r={orbit_r:.3f} "
          f"fovx={math.degrees(fovx):.1f} fovy={math.degrees(fovy):.1f}")

    gaussians = GaussianModel(args.sh_degree)
    gaussians.load_ply(args.ply)
    print(f"loaded {gaussians.get_xyz.shape[0]} gaussians from {args.ply}")

    pipe = Namespace(debug=False, antialiasing=False,
                     compute_cov3D_python=False, convert_SHs_python=False)
    bg = torch.tensor([1.0, 1.0, 1.0] if args.white_bg else [0.0, 0.0, 0.0],
                      dtype=torch.float32, device="cuda")

    h_min = mean_h - 0.3 * radius
    h_max = mean_h + 0.5 * radius

    from torchvision.utils import save_image

    for i in range(args.n_frames):
        t = i / max(1, args.n_frames - 1)
        azim = 2 * math.pi * args.turns * t
        height = h_min + (h_max - h_min) * (0.5 + 0.5 * math.sin(2 * math.pi * t))
        cam_pos = np.array([
            center[0] + orbit_r * math.cos(azim),
            height,
            center[2] + orbit_r * math.sin(azim),
        ], dtype=np.float64)

        cam = build_minicam(MiniCam, getWorld2View2, getProjectionMatrix,
                            cam_pos, target, fovx, fovy, args.width, args.height)
        with torch.no_grad():
            out = render(cam, gaussians, pipe, bg)
        save_image(out["render"].clamp(0, 1), str(frames_dir / f"{i:05d}.png"))
        if (i + 1) % 30 == 0 or i == 0:
            print(f"  frame {i + 1}/{args.n_frames} azim={math.degrees(azim):.0f}")

    print("encoding video ...")
    cmd = [
        "ffmpeg", "-y", "-framerate", str(args.fps),
        "-i", str(frames_dir / "%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "18",
        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        str(args.out_video),
    ]
    subprocess.run(cmd, check=True)
    print(f"video -> {args.out_video}")


if __name__ == "__main__":
    main()
