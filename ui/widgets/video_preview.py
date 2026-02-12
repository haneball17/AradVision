"""
视频预览组件

显示实时捕获的游戏画面。

Author: haneball17
Date: 2026-02-11
"""

# 尝试导入 cv2，如果不可用则跳过相关功能
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    import numpy as np

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QImage, QPixmap, QPainter


class VideoPreviewWidget(QLabel):
    """
    视频预览组件

    显示实时捕获的游戏画面，支持：
    - OpenCV 图像转 QImage 显示
    - 保持宽高比缩放
    - 占位符文本显示
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 固定尺寸
        self.setFixedSize(640, 480)
        self.setAlignment(Qt.AlignCenter)

        # 初始样式
        self.setStyleSheet("""
            VideoPreviewWidget {
                border: 2px solid #555555;
                background-color: #1E1E1E;
                color: #888888;
            }
        """)

        # 显示占位符文本
        self.setPlaceholderText("等待系统启动...")

        # 当前图像
        self.current_pixmap = None

    def setPlaceholderText(self, text: str):
        """
        设置占位符文本

        Args:
            text: 占位符文本
        """
        self.setText(text)
        self.current_pixmap = None

    def update_frame(self, frame):
        """
        更新帧显示

        Args:
            frame: OpenCV 图像 (BGR 格式) 或 None
        """
        if frame is None:
            self.setText("无信号")
            return

        if not HAS_CV2:
            # cv2 不可用时显示占位符
            self.setText(f"帧数据: {type(frame).__name__}")
            return

        try:
            # 转换 BGR 到 RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # 获取图像尺寸
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w

            # 创建 QImage
            qt_image = QImage(
                rgb_image.data,
                w,
                h,
                bytes_per_line,
                QImage.Format_RGB888
            ).copy()

            # 缩放到组件大小（保持宽高比）
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            # 更新显示
            self.setPixmap(scaled_pixmap)
            self.current_pixmap = scaled_pixmap

            # 清除文本
            if self.text():
                self.clear()

        except Exception as e:
            # 显示错误信息
            self.setText(f"预览错误: {str(e)}")

    def clear_frame(self):
        """清除当前帧"""
        self.clear()
        self.current_pixmap = None
        self.setPlaceholderText("等待系统启动...")

    def sizeHint(self):
        """推荐大小"""
        return QSize(640, 480)
