#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ASSET_PLAN = {
    "background": {
        "selection": "Mip-NeRF 360 / counter",
        "target_dir": "assets/offline_inputs/background/mipnerf360_counter",
        "source_url": "https://jonbarron.info/mipnerf360/",
        "notes": [
            "Download the counter scene on a machine with internet access.",
            "Extract the scene under the target_dir path.",
        ],
    },
    "object_a": {
        "selection": "Objectron / cereal_box",
        "target_dir": "assets/offline_inputs/object_a",
        "source_url": "https://github.com/google-research-datasets/Objectron",
        "notes": [
            "Choose a cereal_box sequence with a smooth handheld orbit.",
            "Export frames or images into the target_dir path.",
        ],
    },
    "object_c": {
        "selection": "Objectron / shoe",
        "target_dir": "assets/offline_inputs/object_c",
        "source_url": "https://github.com/google-research-datasets/Objectron",
        "notes": [
            "Pick one clear frame from a shoe sequence.",
            "Store the raw image as object_c_raw.png and the RGBA cutout as object_c_rgba.png.",
        ],
    },
    "weights": {
        "stable_zero123": {
            "target_dir": "assets/offline_weights/stable-zero123",
            "source_url": "https://huggingface.co/stabilityai/stable-zero123",
            "notes": [
                "Place stable-zero123.ckpt under the target_dir.",
                "Expect roughly 7 GB of storage for the main checkpoint.",
            ],
        },
        "text_to_3d": {
            "target_dir": "assets/offline_weights/text_to_3d",
            "source_url": "manual package",
            "notes": [
                "Bundle the selected Stable Diffusion guidance weights for threestudio.",
                "Plan for roughly 5-9 GB depending on chosen model family.",
            ],
        },
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Echo the offline asset acquisition plan.")
    parser.add_argument("--project-root", default=".")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    payload = {
        "project_root": str(project_root),
        "asset_plan": ASSET_PLAN,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
