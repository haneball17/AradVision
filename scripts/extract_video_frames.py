"""
按指定时间点从视频导出原始帧。

适用场景：
1. 基于视频分析文档批量导出关键截图
2. 为 ROI、状态阈值和房间脚本复核准备统一命名的样本
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import cv2
except ImportError as exc:  # pragma: no cover - 依赖由运行环境决定
    raise SystemExit("缺少 opencv-python，无法导出视频帧") from exc


@dataclass(frozen=True)
class FrameSpec:
    """单个导出时间点。"""

    seconds: float
    label: str


def parse_time_to_seconds(raw: str) -> float:
    """
    解析时间字符串。

    支持格式：
    - SS
    - MM:SS
    - HH:MM:SS
    """
    text = raw.strip()
    if not text:
        raise ValueError("时间点不能为空")

    if re.fullmatch(r"\d+(\.\d+)?", text):
        return float(text)

    parts = text.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    raise ValueError(f"无法解析时间格式: {raw}")


def format_mm_ss(seconds: float) -> str:
    """格式化为 mm-ss。"""
    total = int(round(seconds))
    minutes = total // 60
    remain = total % 60
    return f"{minutes:02d}-{remain:02d}"


def sanitize_label(label: str) -> str:
    """将标签归一化为适合文件名的 ASCII。"""
    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "_", label.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "frame"


def parse_specs_from_lines(lines: Iterable[str]) -> List[FrameSpec]:
    """从文本行解析时间点。"""
    specs: List[FrameSpec] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = re.split(r"\s+", line, maxsplit=1)
        seconds = parse_time_to_seconds(parts[0])
        label = parts[1] if len(parts) > 1 else f"frame_{format_mm_ss(seconds)}"
        specs.append(FrameSpec(seconds=seconds, label=sanitize_label(label)))
    return specs


def load_specs(args: argparse.Namespace) -> List[FrameSpec]:
    """加载时间点配置。"""
    specs: List[FrameSpec] = []
    if args.times:
        specs.extend(parse_specs_from_lines(args.times.split(",")))

    if args.times_file:
        with open(args.times_file, "r", encoding="utf-8") as fh:
            specs.extend(parse_specs_from_lines(fh))

    if not specs:
        raise ValueError("至少需要提供 --times 或 --times-file")

    dedup: dict[tuple[int, str], FrameSpec] = {}
    for spec in specs:
        key = (int(round(spec.seconds * 1000)), spec.label)
        dedup[key] = spec
    return sorted(dedup.values(), key=lambda item: item.seconds)


def extract_frames(
    video_path: Path,
    output_dir: Path,
    specs: List[FrameSpec],
    prefix: str,
) -> List[Path]:
    """执行导出。"""
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"无法打开视频: {video_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []
    try:
        for spec in specs:
            capture.set(cv2.CAP_PROP_POS_MSEC, spec.seconds * 1000)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"无法读取时间点 {spec.seconds:.2f}s 的帧")

            filename = f"{prefix}_{format_mm_ss(spec.seconds)}_{spec.label}.png"
            target = output_dir / filename
            if not cv2.imwrite(str(target), frame):
                raise RuntimeError(f"写入失败: {target}")
            written.append(target)
    finally:
        capture.release()

    return written


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数。"""
    parser = argparse.ArgumentParser(description="按指定时间点从视频导出原始帧")
    parser.add_argument("--video", required=True, help="输入视频路径")
    parser.add_argument("--output", required=True, help="输出目录")
    parser.add_argument(
        "--times",
        help="逗号分隔的时间点列表，格式如 '00:12 transition,00:30 combat'",
    )
    parser.add_argument(
        "--times-file",
        help="时间点清单文件，每行格式：<时间> <标签>",
    )
    parser.add_argument(
        "--prefix",
        default="video_frame",
        help="输出文件名前缀，默认 video_frame",
    )
    return parser


def main() -> int:
    """脚本入口。"""
    parser = build_parser()
    args = parser.parse_args()

    video_path = Path(args.video).expanduser().resolve()
    output_dir = Path(args.output).expanduser().resolve()
    prefix = sanitize_label(args.prefix)

    if not video_path.exists():
        raise SystemExit(f"视频不存在: {video_path}")

    specs = load_specs(args)
    written = extract_frames(video_path, output_dir, specs, prefix)

    print(f"已导出 {len(written)} 张截图到: {output_dir}")
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
