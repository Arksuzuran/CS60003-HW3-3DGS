#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def quat_normalize(q: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(q, axis=1, keepdims=True)
    norms = np.clip(norms, 1e-12, None)
    return q / norms


def quat_mul(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = q1.T
    w2, x2, y2, z2 = q2.T
    return np.stack(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ],
        axis=1,
    )


def euler_xyz_deg_to_matrix(euler_deg: list[float]) -> np.ndarray:
    rx, ry, rz = np.deg2rad(euler_deg)
    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)
    rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32)
    rot_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32)
    return rot_z @ rot_y @ rot_x


def matrix_to_quat_wxyz(rot: np.ndarray) -> np.ndarray:
    m = rot
    trace = np.trace(m)
    if trace > 0:
        s = np.sqrt(trace + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    quat = np.array([w, x, y, z], dtype=np.float32)
    quat /= np.linalg.norm(quat) + 1e-12
    return quat


def load_config(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import yaml  # type: ignore

        return yaml.safe_load(text)


def load_vertex_table(path: Path) -> np.ndarray:
    from plyfile import PlyData  # type: ignore

    ply = PlyData.read(str(path))
    return ply["vertex"].data


def transform_vertex_table(
    table: np.ndarray,
    translation: list[float],
    rotation_euler_deg: list[float],
    scale: float,
) -> np.ndarray:
    out = np.array(table, copy=True)
    rot_m = euler_xyz_deg_to_matrix(rotation_euler_deg)
    rot_q = matrix_to_quat_wxyz(rot_m)[None, :]

    xyz = np.stack([out["x"], out["y"], out["z"]], axis=1).astype(np.float32)
    xyz = (xyz @ rot_m.T) * scale + np.asarray(translation, dtype=np.float32)
    out["x"] = xyz[:, 0]
    out["y"] = xyz[:, 1]
    out["z"] = xyz[:, 2]

    scale_cols = [name for name in out.dtype.names if name.startswith("scale_")]
    if scale_cols:
        raw = np.stack([out[name] for name in scale_cols], axis=1).astype(np.float32)
        actual = np.exp(raw)
        actual *= scale
        raw_new = np.log(np.clip(actual, 1e-12, None))
        for idx, name in enumerate(scale_cols):
            out[name] = raw_new[:, idx]

    rot_cols = [name for name in out.dtype.names if name.startswith("rot_")]
    if rot_cols and len(rot_cols) == 4:
        raw_q = np.stack([out[name] for name in rot_cols], axis=1).astype(np.float32)
        raw_q = quat_normalize(raw_q)
        new_q = quat_mul(np.repeat(rot_q, raw_q.shape[0], axis=0), raw_q)
        new_q = quat_normalize(new_q)
        for idx, name in enumerate(rot_cols):
            out[name] = new_q[:, idx]

    return out


def concatenate_tables(tables: list[np.ndarray]) -> np.ndarray:
    if not tables:
        raise ValueError("No vertex tables provided for merge.")
    names = tables[0].dtype.names
    for table in tables[1:]:
        if table.dtype.names != names:
            raise ValueError("PLY schemas do not match; cannot merge safely.")
    return np.concatenate(tables, axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge multiple gaussian assets by config.")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--asset-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--config", default="configs/fusion.yaml")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root)
    config = load_config(project_root / args.config)
    output_root = Path(args.output_root)
    fused_root = output_root / "fusion"
    if not args.dry_run:
        fused_root.mkdir(parents=True, exist_ok=True)

    merged_tables = []
    background_path = Path(config["fusion"]["background"]["gaussian_path"])
    if background_path.exists():
        merged_tables.append(load_vertex_table(background_path))

    for obj_cfg in config["fusion"]["objects"]:
        obj_path = Path(obj_cfg["gaussian_path"])
        if obj_path.exists():
            merged_tables.append(
                transform_vertex_table(
                    load_vertex_table(obj_path),
                    translation=obj_cfg["translation"],
                    rotation_euler_deg=obj_cfg["rotation_euler_deg"],
                    scale=float(obj_cfg["scale"]),
                )
            )

    fused_ply = fused_root / "merged_gaussians.ply"
    metadata_path = fused_root / "merge_plan.json"

    if merged_tables and not args.dry_run:
        from plyfile import PlyData, PlyElement  # type: ignore

        merged = concatenate_tables(merged_tables)
        PlyData([PlyElement.describe(merged, "vertex")], text=False).write(str(fused_ply))
        metadata_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "background": config["fusion"]["background"],
        "objects": config["fusion"]["objects"],
        "render": config["fusion"]["render"],
        "fused_root": str(fused_root),
        "fused_ply": str(fused_ply),
        "metadata_path": str(metadata_path),
        "loaded_tables": len(merged_tables),
        "dry_run": args.dry_run,
        "notes": [
            "This script applies rigid transforms to xyz, scale parameters and quaternion rotations.",
            "Background is loaded as-is; objects are transformed according to configs/fusion.yaml.",
        ],
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
