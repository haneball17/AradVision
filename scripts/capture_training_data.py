"""
数据收集脚本 - 自动截取游戏画面用于YOLO训练

使用方法:
1. 启动游戏并确保窗口标题为 "Dungeon & Fighter"
2. 运行此脚本: python scripts/capture_training_data.py
3. 在游戏中进行各种操作（战斗、拾取、过图）
4. 按 F12 停止收集

Author: Dev A
Date: Day 1
"""

import cv2
import time
import win32gui
import numpy as np
from mss import mss
from pathlib import Path
import keyboard

class DataCollector:
    """自动游戏截图收集器"""

    def __init__(self, window_title: str = "Dungeon & Fighter"):
        self.window_title = window_title
        self.output_dir = Path("assets/images/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.sct = mss()
        self.hwnd = None
        self.running = False
        self.frame_count = 0
        self.last_capture_time = 0
        self.capture_interval = 0.5  # 每0.5秒截一张

    def find_window(self) -> bool:
        """查找游戏窗口"""
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.window_title.lower() in title.lower():
                    self.hwnd = hwnd
                    return False
            return True

        win32gui.EnumWindows(callback, None)
        return self.hwnd is not None

    def get_window_rect(self) -> dict:
        """获取窗口区域"""
        rect = win32gui.GetWindowRect(self.hwnd)
        return {
            "left": rect[0],
            "top": rect[1],
            "width": rect[2] - rect[0],
            "height": rect[3] - rect[1]
        }

    def capture_frame(self) -> np.ndarray:
        """截取单帧画面"""
        monitor = self.get_window_rect()
        screenshot = self.sct.grab(monitor)

        # 转换为OpenCV格式 (BGR)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        return frame

    def save_frame(self, frame: np.ndarray, category: str = "general"):
        """保存帧到文件"""
        category_dir = self.output_dir / category
        category_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = category_dir / f"{category}_{timestamp}_{self.frame_count:06d}.jpg"

        cv2.imwrite(str(filename), frame)
        self.frame_count += 1

        return filename

    def start(self):
        """开始收集数据"""
        if not self.find_window():
            print(f"❌ 未找到窗口: {self.window_title}")
            print("请确保游戏已启动")
            return False

        print(f"✅ 找到窗口: {win32gui.GetWindowText(self.hwnd)}")
        print(f"📁 保存目录: {self.output_dir.absolute()}")
        print(f"⏱️  采集间隔: {self.capture_interval}秒")
        print(f"🎮 开始收集... 按 F12 停止\n")

        self.running = True

        # 监听F12停止键
        keyboard.on_press_key("F12", self._stop_callback)

        while self.running:
            current_time = time.time()

            # 控制采集频率
            if current_time - self.last_capture_time >= self.capture_interval:
                try:
                    frame = self.capture_frame()

                    # 根据场景自动分类（简单的亮度检测）
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    brightness = gray.mean()

                    if brightness < 50:
                        category = "dark"  # 暗场景
                    elif brightness > 200:
                        category = "bright"  # 亮场景
                    else:
                        category = "normal"  # 正常场景

                    filename = self.save_frame(frame, category)

                    print(f"📸 [{self.frame_count:04d}] {filename.name} (亮度: {brightness:.0f})")

                    self.last_capture_time = current_time

                except Exception as e:
                    print(f"❌ 截图失败: {e}")
                    time.sleep(1)

            time.sleep(0.1)  # 减少CPU占用

        print(f"\n✅ 收集完成! 共 {self.frame_count} 张图片")
        return True

    def _stop_callback(self, _):
        """F12停止回调"""
        self.running = False

def main():
    """主函数"""
    print("=" * 60)
    print("       AradVision - 数据收集工具")
    print("=" * 60)
    print()

    collector = DataCollector()
    collector.start()

if __name__ == "__main__":
    main()
