"""WGC/MSS 捕获后端人工验证脚本。

用途：
1. 快速验证后端是否可启动。
2. 采样保存若干帧，便于比较遮挡场景行为。

示例：
    python3 scripts/verify_capture_backend.py --backend auto --frames 60
    python3 scripts/verify_capture_backend.py --backend wgc --window-title "DNF Taiwan"
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from core.capture import create_capture_engine
from core.config import ConfigLoader
from core.logger import logger, setup_logger


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="验证捕获后端行为")
    parser.add_argument("--config", default="configs/config.yaml", help="配置文件路径")
    parser.add_argument("--backend", choices=["auto", "wgc", "mss"], default=None)
    parser.add_argument("--window-title", default=None, help="覆盖配置中的窗口标题")
    parser.add_argument("--frames", type=int, default=30, help="采样帧数")
    parser.add_argument("--interval", type=float, default=0.05, help="采样间隔（秒）")
    parser.add_argument("--output-dir", default="logs/capture_verify", help="输出目录")
    parser.add_argument("--use-mock", action="store_true", help="使用 Mock 捕获")
    return parser.parse_args()


def main() -> int:
    """脚本主入口。"""
    args = parse_args()
    setup_logger(log_level="INFO")

    loader = ConfigLoader.instance()
    cfg = loader.load(args.config)

    capture_cfg = cfg.capture
    if args.backend is not None:
        capture_cfg.backend = args.backend
    if args.window_title:
        capture_cfg.window_title = args.window_title

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "开始验证捕获后端: "
        f"requested_backend={capture_cfg.backend}, "
        f"window_title={capture_cfg.window_title}, frames={args.frames}"
    )

    engine = create_capture_engine(
        config=capture_cfg,
        use_mock=args.use_mock or capture_cfg.use_mock,
        backend=capture_cfg.backend,
    )

    saved = 0
    try:
        engine.start()
        active_backend = getattr(engine, "active_backend", "unknown")
        logger.info(f"捕获引擎启动成功: active_backend={active_backend}")

        try:
            import cv2
        except ImportError:
            cv2 = None  # type: ignore
            logger.warning("cv2 不可用，本次仅采样不落盘")

        for i in range(args.frames):
            frame = engine.get_frame()
            logger.info(f"frame[{i}] shape={getattr(frame, 'shape', None)}")

            if cv2 is not None and frame is not None:
                file_path = output_dir / f"frame_{i:04d}.jpg"
                cv2.imwrite(str(file_path), frame)
                saved += 1

            time.sleep(max(0.0, args.interval))

        stats = engine.get_stats()
        logger.info(
            "验证完成: "
            f"saved={saved}, frame_count={stats.frame_count}, fps={stats.fps:.2f}, "
            f"avg_latency={stats.avg_latency:.2f}ms"
        )
        return 0

    except Exception as exc:
        logger.error(f"验证失败: {exc}", exc_info=True)
        return 1

    finally:
        try:
            engine.stop()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
