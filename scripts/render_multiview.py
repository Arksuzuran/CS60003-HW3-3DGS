#!/usr/bin/env python3
"""Render an exported mesh from many viewpoints with nvdiffrast and emit a
NeRF-Synthetic / Blender style dataset (images + transforms_*.json) that the
gaussian-splatting trainer can consume directly.

This is the bridge that turns the generated 3D assets (object B from
text-to-3D, object C from single-image-to-3D) into a *unified* 3D Gaussian
representation: mesh -> multi-view renders -> 3DGS.

Run with the gen3d environment python (nvdiffrast lives there)::

    python render_multiview.py --mesh <model.obj> --out <dataset_dir>

Notes
-----
* RGB channels store the *raw* shaded color; the alpha channel stores the
  coverage mask. The 3DGS Blender loader composites RGB over the configured
  background using this alpha, so we must not pre-multiply a background here.
* Cameras are placed on a sphere using a Fibonacci spiral so that elevation and
  azimuth are well distributed, which gives 3DGS dense angular coverage.
"""
from __future__ import annotations

import argparse
import json
from math import cos, pi, sin
from pathlib import Path

import numpy as np
import nvdiffrast.torch as dr
import torch
import trimesh
from PIL import Image


def load_mesh(mesh_path: str):
    mesh = trimesh.load(mesh_path, process=False)
    if isinstance(mesh, trimesh.Scene):
        meshes = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("No Trimesh objects found in scene")
        mesh = max(meshes, key=lambda m: len(m.vertices))
        print(f"  Scene flattened, using mesh with {len(mesh.vertices)} verts")

    verts = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)

    uv = None
    texture = None
    vertex_colors = None

    visual_kind = getattr(mesh.visual, "kind", None)
    if visual_kind == "texture":
        if getattr(mesh.visual, "uv", None) is not None:
            uv = mesh.visual.uv.astype(np.float32)
        mat = mesh.visual.material
        img = getattr(mat, "image", None) if mat is not None else None
        if img is None and mat is not None:
            img = getattr(mat, "baseColorTexture", None)
        if img is not None:
            if img.mode != "RGB":
                img = img.convert("RGB")
            texture = np.array(img, dtype=np.float32) / 255.0
            print(f"  Texture: {texture.shape}, UV: {None if uv is None else uv.shape}")

    if visual_kind == "vertex" or (texture is None and uv is None):
        vc = getattr(mesh.visual, "vertex_colors", None)
        if vc is not None and len(vc) == len(verts):
            vertex_colors = np.array(vc, dtype=np.float32) / 255.0
            if vertex_colors.shape[-1] == 4:
                vertex_colors = vertex_colors[..., :3]
            print(f"  Vertex colors: {vertex_colors.shape}")

    if texture is None and vertex_colors is None:
        print("  No texture/vertex colors found, falling back to neutral gray")
        vertex_colors = np.full((len(verts), 3), 0.7, dtype=np.float32)

    return verts, faces, uv, texture, vertex_colors


def look_at(eye: np.ndarray, center: np.ndarray, up: np.ndarray) -> np.ndarray:
    """OpenGL world-to-camera matrix (camera looks along -Z)."""
    f = center - eye
    fnorm = np.linalg.norm(f)
    f = f / fnorm if fnorm > 1e-12 else np.array([0.0, 0.0, -1.0], dtype=np.float32)
    s = np.cross(f, up)
    snorm = np.linalg.norm(s)
    s = s / snorm if snorm > 1e-12 else np.array([1.0, 0.0, 0.0], dtype=np.float32)
    u = np.cross(s, f)

    view = np.eye(4, dtype=np.float32)
    view[0, :3] = s
    view[1, :3] = u
    view[2, :3] = -f
    view[0, 3] = -float(np.dot(s, eye))
    view[1, 3] = -float(np.dot(u, eye))
    view[2, 3] = float(np.dot(f, eye))
    return view


def view_to_blender_c2w(view: np.ndarray) -> np.ndarray:
    R = view[:3, :3]
    t = view[:3, 3]
    c2w = np.eye(4, dtype=np.float32)
    c2w[:3, :3] = R.T
    c2w[:3, 3] = -R.T @ t
    return c2w


def perspective(fov_y: float, aspect: float, z_near: float = 0.01, z_far: float = 100.0):
    f = 1.0 / np.tan(fov_y / 2.0)
    proj = np.zeros((4, 4), dtype=np.float32)
    proj[0, 0] = f / aspect
    proj[1, 1] = f
    proj[2, 2] = -(z_far + z_near) / (z_far - z_near)
    proj[2, 3] = -2.0 * z_far * z_near / (z_far - z_near)
    proj[3, 2] = -1.0
    return proj


def render_view(glctx, verts, faces, uv, texture, vertex_colors, view, proj, resolution):
    H, W = resolution
    mvp = proj @ view
    v_hom = np.concatenate([verts, np.ones((verts.shape[0], 1), dtype=np.float32)], axis=-1)
    v_clip = v_hom @ mvp.T
    v_clip_tensor = torch.from_numpy(v_clip[None, ...]).cuda()
    faces_tensor = torch.from_numpy(faces).cuda()

    raster_out, _ = dr.rasterize(glctx, v_clip_tensor, faces_tensor, (H, W))
    mask = raster_out[..., 3:4] > 0

    if texture is not None and uv is not None:
        uv_tensor = torch.from_numpy(uv[None, ...]).cuda()
        uv_interp, _ = dr.interpolate(uv_tensor, raster_out, faces_tensor)
        tex_tensor = torch.from_numpy(texture[None, ...]).cuda()
        color = dr.texture(tex_tensor, uv_interp)
    else:
        colors_tensor = torch.from_numpy(vertex_colors[None, ...]).cuda()
        color, _ = dr.interpolate(colors_tensor, raster_out, faces_tensor)

    color = color.clamp(0.0, 1.0)
    return color[0], mask[0].float()


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-view mesh renderer for 3DGS")
    parser.add_argument("--mesh", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--n_views", type=int, default=120)
    parser.add_argument("--resolution", type=int, default=800)
    parser.add_argument("--fov_y", type=float, default=45.0)
    parser.add_argument("--radius", type=float, default=2.6)
    parser.add_argument("--elev_range", type=float, nargs=2, default=[-15.0, 70.0])
    parser.add_argument("--test_frac", type=float, default=0.1,
                        help="Fraction of views held out into transforms_test.json")
    args = parser.parse_args()

    out_dir = Path(args.out)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Loading mesh: {args.mesh}")
    verts, faces, uv, texture, vertex_colors = load_mesh(args.mesh)

    print(f"[2/4] Normalizing mesh ({len(verts)} verts, {len(faces)} faces)")
    center = verts.mean(axis=0)
    verts = verts - center
    max_ext = float(np.max(np.linalg.norm(verts, axis=1)))
    if max_ext > 1e-9:
        verts = verts / max_ext
    print(f"  Centered at {center}, max_extent={max_ext:.4f}")

    print("[3/4] Setting up nvdiffrast")
    try:
        glctx = dr.RasterizeCudaContext()
    except Exception as exc:  # pragma: no cover - depends on driver
        print(f"  CudaContext failed ({exc}); falling back to GL context")
        glctx = dr.RasterizeGLContext()

    fov_y_rad = np.deg2rad(args.fov_y)
    res = (args.resolution, args.resolution)
    proj = perspective(fov_y_rad, 1.0)

    print(f"[4/4] Rendering {args.n_views} views")
    elev_min = np.deg2rad(args.elev_range[0])
    elev_max = np.deg2rad(args.elev_range[1])
    golden = (1 + 5 ** 0.5) / 2
    frames = []

    for i in range(args.n_views):
        t = i / (args.n_views - 1) if args.n_views > 1 else 0.5
        elev = elev_min + t * (elev_max - elev_min)
        azim = 2 * pi * i / golden
        eye = np.array(
            [
                args.radius * cos(elev) * cos(azim),
                args.radius * sin(elev),
                args.radius * cos(elev) * sin(azim),
            ],
            dtype=np.float32,
        )
        view = look_at(eye, np.zeros(3, dtype=np.float32), np.array([0.0, 1.0, 0.0], dtype=np.float32))
        c2w = view_to_blender_c2w(view)

        color, mask = render_view(glctx, verts, faces, uv, texture, vertex_colors, view, proj, res)
        rgb = (color.cpu().numpy() * 255).astype(np.uint8)
        alpha = (mask.cpu().numpy() * 255).astype(np.uint8)
        rgba = np.concatenate([rgb, alpha], axis=-1)
        Image.fromarray(rgba, mode="RGBA").save(str(images_dir / f"{i:05d}.png"))

        frames.append({"file_path": f"images/{i:05d}", "transform_matrix": c2w.tolist()})
        if (i + 1) % 20 == 0 or i == 0:
            print(f"  {i + 1}/{args.n_views} (elev={np.rad2deg(elev):.0f}, azim={np.rad2deg(azim):.0f})")

    fov_x = 2 * np.arctan(np.tan(fov_y_rad / 2) * 1.0)
    n_test = max(1, int(round(args.n_views * args.test_frac)))
    test_idx = set(np.linspace(0, args.n_views - 1, n_test).round().astype(int).tolist())
    train_frames = [f for i, f in enumerate(frames) if i not in test_idx]
    test_frames = [frames[i] for i in sorted(test_idx)]

    for name, fr in [("train", train_frames), ("test", test_frames), ("val", test_frames)]:
        with (out_dir / f"transforms_{name}.json").open("w") as fh:
            json.dump({"camera_angle_x": float(fov_x), "frames": fr}, fh, indent=2)

    print(f"\nDone -> {out_dir}")
    print(f"  train={len(train_frames)} test={len(test_frames)} fov_x={np.rad2deg(fov_x):.2f}")


if __name__ == "__main__":
    main()
