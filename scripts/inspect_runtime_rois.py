"""
批量检查当前配置下的运行期 ROI。

功能：
1. 对一组截图绘制 ROI overlay
2. 为每张截图导出 ROI crop 联系图
3. 运行 MainViewReader / MinimapReader / StateReader，输出诊断摘要
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Iterable

import cv2

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.config import ConfigLoader
from vision.main_view_reader import MainViewReader
from vision.minimap_reader import MinimapReader
from vision.state_reader import StateReader


ROI_COLORS = {
    "transition_roi": (0, 255, 255),
    "clear_roi": (255, 0, 0),
    "boss_roi": (0, 0, 255),
    "finish_roi": (0, 255, 0),
    "neighbor_roi": (255, 255, 0),
    "special_roi": (255, 0, 255),
    "hp_bar": (0, 128, 255),
    "mp_bar": (255, 128, 0),
    "inventory_flag": (64, 255, 255),
    "inventory_weight_bar": (128, 255, 0),
    "vendor_flag": (128, 0, 255),
    "potion_flag": (0, 128, 128),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="批量检查当前配置下的运行期 ROI")
    parser.add_argument("--images-dir", required=True, help="截图目录")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument(
        "--config",
        default="configs/config.yaml",
        help="配置文件路径，默认 configs/config.yaml",
    )
    return parser


def iter_images(images_dir: Path) -> Iterable[Path]:
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        for path in sorted(images_dir.glob(ext)):
            yield path


def build_roi_specs(config) -> list[tuple[str, object]]:
    return [
        ("transition_roi", config.dungeon_run.main_view.transition_roi),
        ("clear_roi", config.dungeon_run.main_view.clear_roi),
        ("boss_roi", config.dungeon_run.main_view.boss_roi),
        ("finish_roi", config.dungeon_run.main_view.finish_roi),
        ("neighbor_roi", config.dungeon_run.minimap.neighbor_roi),
        ("special_roi", config.dungeon_run.minimap.special_roi),
        ("hp_bar", config.dungeon_run.ui_rois.hp_bar),
        ("mp_bar", config.dungeon_run.ui_rois.mp_bar),
        ("inventory_flag", config.dungeon_run.ui_rois.inventory_flag),
        ("inventory_weight_bar", config.dungeon_run.ui_rois.inventory_weight_bar),
        ("vendor_flag", config.dungeon_run.ui_rois.vendor_flag),
        ("potion_flag", config.dungeon_run.ui_rois.potion_flag),
    ]


def draw_overlay(image, roi_specs):
    output = image.copy()
    for name, roi in roi_specs:
        color = ROI_COLORS[name]
        cv2.rectangle(output, (roi.x, roi.y), (roi.x + roi.w, roi.y + roi.h), color, 2)
        cv2.putText(
            output,
            name,
            (roi.x, max(12, roi.y - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
    return output


def build_crop_contact(image, roi_specs):
    thumbs = []
    for name, roi in roi_specs:
        crop = image[roi.y : roi.y + roi.h, roi.x : roi.x + roi.w]
        if crop.size == 0:
            continue

        scale = min(280 / max(1, crop.shape[1]), 120 / max(1, crop.shape[0]))
        resized = cv2.resize(
            crop,
            (
                max(1, int(crop.shape[1] * scale)),
                max(1, int(crop.shape[0] * scale)),
            ),
            interpolation=cv2.INTER_NEAREST,
        )
        canvas = 255 * (cv2.UMat(120, 280, cv2.CV_8UC3).get())
        y = (120 - resized.shape[0]) // 2
        x = (280 - resized.shape[1]) // 2
        canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
        cv2.putText(
            canvas,
            name,
            (6, 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
        thumbs.append(canvas)

    cols = 2
    rows = math.ceil(len(thumbs) / cols) if thumbs else 1
    contact = 255 * (cv2.UMat(rows * 120, cols * 280, cv2.CV_8UC3).get())
    for index, thumb in enumerate(thumbs):
        row = index // cols
        col = index % cols
        contact[row * 120 : (row + 1) * 120, col * 280 : (col + 1) * 280] = thumb
    return contact


def main() -> int:
    args = build_parser().parse_args()
    images_dir = Path(args.images_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    overlays_dir = output_dir / "overlays"
    crops_dir = output_dir / "crops"
    output_dir.mkdir(parents=True, exist_ok=True)
    overlays_dir.mkdir(parents=True, exist_ok=True)
    crops_dir.mkdir(parents=True, exist_ok=True)

    loader = ConfigLoader.instance()
    config = loader.load(args.config)
    roi_specs = build_roi_specs(config)
    main_reader = MainViewReader(config.dungeon_run.main_view)
    minimap_reader = MinimapReader(config.dungeon_run.minimap)
    state_reader = StateReader(config.dungeon_run.ui_rois)

    summary_path = output_dir / "reader_summary.csv"
    with open(summary_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "image",
                "main_state",
                "minimap_path_state",
                "minimap_special_state",
                "hp_percent",
                "mp_percent",
                "inventory_weight_ratio",
                "vendor_ui_open",
                "potion_cd_ready",
                "potion_stock_available",
            ]
        )

        for image_path in iter_images(images_dir):
            image = cv2.imread(str(image_path))
            if image is None:
                continue

            overlay = draw_overlay(image, roi_specs)
            cv2.imwrite(str(overlays_dir / image_path.name), overlay)

            contact = build_crop_contact(image, roi_specs)
            cv2.imwrite(str(crops_dir / image_path.name), contact)

            main_state = main_reader.read(image)
            path_state, special_state = minimap_reader.read(
                image,
                expected_room_index=1,
                is_last_normal_room=False,
            )
            state = state_reader.read(image)
            writer.writerow(
                [
                    image_path.name,
                    main_state.value,
                    path_state.value,
                    special_state.value,
                    f"{state.player_state.hp_percent:.4f}",
                    f"{state.player_state.mp_percent:.4f}",
                    f"{state.inventory_weight_ratio:.4f}",
                    str(state.vendor_ui_open),
                    str(state.potion_cd_ready),
                    str(state.potion_stock_available),
                ]
            )

    print(f"诊断输出目录: {output_dir}")
    print(f"摘要文件: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
