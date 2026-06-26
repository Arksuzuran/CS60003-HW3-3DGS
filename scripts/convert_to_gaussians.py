#!/usr/bin/env python3
"""Convert a threestudio-generated asset (object B text-to-3D, object C
single-image-to-3D) into a unified 3D Gaussian Splatting representation.

Pipeline (per object)::

    threestudio checkpoint
        -> [threestudio --export]   mesh (obj + baked texture)
        -> [render_multiview.py]    multi-view RGBA + transforms_*.json
        -> [gaussian-splatting]     point_cloud.ply (iteration_30000)

The threestudio export + rendering run in the gen3d environment (nvdiffrast),
while the 3DGS training runs in the gsbg2 environment. This orchestrator simply
drives the three subprocess stages with the correct interpreter for each.

Example::

    python scripts/convert_to_gaussians.py \
        --project-root "$PWD" --output-root "$PWD/outputs" --object b
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PUBLIC = "/inspire/hdd/project/fdu-aidake-cfff/public"
GS_ENV = os.environ.get("GS_ENV", f"{PUBLIC}/.conda/envs/gsbg2")
T3D_ENV = os.environ.get("T3D_ENV", f"{PUBLIC}/.conda/envs/gen3d")
GS_PY = f"{GS_ENV}/bin/python"
T3D_PY = f"{T3D_ENV}/bin/python"

# threestudio system "name" field used to build the run directory.
OBJECT_SYSTEM_NAME = {"b": "dreamfusion-sd", "c": "zero123-simple"}


def run(cmd: list[str], cwd: str | None = None, env: dict | None = None) -> None:
    printable = " ".join(cmd)
    print(f"\n$ {printable}\n", flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_run_dir(object_root: Path, system_name: str) -> Path:
    """Locate the latest threestudio run dir holding a checkpoint."""
    search_roots = [object_root / system_name, object_root]
    candidates: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for ckpt in root.glob("**/ckpts/last.ckpt"):
            candidates.append(ckpt.parent.parent)
    if not candidates:
        raise FileNotFoundError(
            f"No threestudio checkpoint (ckpts/last.ckpt) found under {object_root}"
        )
    candidates.sort(key=lambda p: p.stat().st_mtime)
    chosen = candidates[-1]
    print(f"  run_dir = {chosen}")
    return chosen


def export_mesh(run_dir: Path, threestudio_root: Path) -> Path:
    parsed_cfg = run_dir / "configs" / "parsed.yaml"
    ckpt = run_dir / "ckpts" / "last.ckpt"
    if not parsed_cfg.exists() or not ckpt.exists():
        raise FileNotFoundError(f"Missing parsed.yaml/last.ckpt in {run_dir}")

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    cmd = [
        T3D_PY,
        "launch.py",
        "--config",
        str(parsed_cfg),
        "--export",
        "--gpu",
        "0",
        f"resume={ckpt}",
        "system.exporter_type=mesh-exporter",
        "system.exporter.fmt=obj-mtl",
        "system.exporter.context_type=cuda",
        "system.geometry.isosurface_method=mc-cpu",
        "system.geometry.isosurface_resolution=192",
        "system.geometry.isosurface_threshold=auto",
    ]
    run(cmd, cwd=str(threestudio_root), env=env)

    meshes = sorted((run_dir / "save").glob("it*-export/model.obj"),
                    key=lambda p: p.stat().st_mtime)
    if not meshes:
        raise FileNotFoundError(f"Mesh export produced no model.obj under {run_dir/'save'}")
    mesh = meshes[-1]
    print(f"  exported mesh = {mesh}")
    return mesh


def render_dataset(mesh: Path, dataset_dir: Path, scripts_dir: Path) -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    cmd = [
        T3D_PY,
        str(scripts_dir / "render_multiview.py"),
        "--mesh",
        str(mesh),
        "--out",
        str(dataset_dir),
        "--n_views",
        "150",
        "--resolution",
        "800",
    ]
    run(cmd, env=env)


def train_gaussians(dataset_dir: Path, model_dir: Path, gs_root: Path,
                    iterations: int, port: int, white_background: bool = False) -> Path:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    cmd = [
        GS_PY,
        "train.py",
        "-s",
        str(dataset_dir),
        "-m",
        str(model_dir),
        "--iterations",
        str(iterations),
        "--port",
        str(port),
    ]
    if white_background:
        cmd.append("--white_background")
    run(cmd, cwd=str(gs_root), env=env)
    ply = model_dir / "point_cloud" / f"iteration_{iterations}" / "point_cloud.ply"
    if not ply.exists():
        raise FileNotFoundError(f"3DGS training did not produce {ply}")
    print(f"  gaussian ply = {ply}")
    return ply


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert B/C assets into 3D Gaussians.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--object", choices=["b", "c"], required=True)
    parser.add_argument("--iterations", type=int, default=30000)
    parser.add_argument("--port", type=int, default=6020)
    parser.add_argument("--white-background", action="store_true", default=False,
                        help="Use white background when loading Blender synthetic data.")
    parser.add_argument("--skip-export", action="store_true",
                        help="Reuse an already exported mesh if present.")
    parser.add_argument("--skip-render", action="store_true",
                        help="Reuse an already rendered dataset if present.")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    output_root = Path(args.output_root)
    scripts_dir = project_root / "scripts"
    threestudio_root = Path(os.environ.get("THREESTUDIO_ROOT",
                                           project_root / "third_party" / "threestudio"))
    gs_root = Path(os.environ.get("GAUSSIAN_SPLATTING_ROOT",
                                  project_root / "third_party" / "gaussian-splatting"))

    obj = args.object
    object_root = output_root / f"object_{obj}"
    dataset_dir = output_root / f"object_{obj}_gaussian_dataset"
    model_dir = output_root / f"object_{obj}_gaussian"

    print(f"[convert] object={obj} system={OBJECT_SYSTEM_NAME[obj]}")
    run_dir = find_run_dir(object_root, OBJECT_SYSTEM_NAME[obj])

    mesh: Path | None = None
    if args.skip_export:
        existing = sorted((run_dir / "save").glob("it*-export/model.obj"),
                          key=lambda p: p.stat().st_mtime)
        mesh = existing[-1] if existing else None
    if mesh is None:
        mesh = export_mesh(run_dir, threestudio_root)

    if not (args.skip_render and (dataset_dir / "transforms_train.json").exists()):
        render_dataset(mesh, dataset_dir, scripts_dir)

    ply = train_gaussians(dataset_dir, model_dir, gs_root, args.iterations, args.port,
                          white_background=args.white_background)

    print(f"\n[convert] object {obj} -> {ply}")


if __name__ == "__main__":
    sys.exit(main())
