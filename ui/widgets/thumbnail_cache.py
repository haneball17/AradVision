"""
缩略图缓存工具

用于统一管理缩略图解码与内存缓存，减少重复读取磁盘图片造成的卡顿。
"""

from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QImageReader, QPainter, QPixmap


class ThumbnailCache:
    """简单 LRU 缩略图缓存。"""

    def __init__(self, thumbnail_size: QSize, max_items: int = 512):
        self._thumbnail_size = thumbnail_size
        self._max_items = max(64, max_items)
        self._cache: "OrderedDict[str, QPixmap]" = OrderedDict()
        self._placeholder = self._build_placeholder()

    def clear(self) -> None:
        """清空缓存。"""
        self._cache.clear()

    def placeholder(self) -> QPixmap:
        """返回统一占位图。"""
        return self._placeholder

    def get(self, image_path: str) -> QPixmap:
        """获取缩略图，命中失败时尝试解码并写入缓存。"""
        path = str(image_path).strip()
        if not path:
            return self._placeholder

        cached = self._cache.get(path)
        if cached is not None:
            self._cache.move_to_end(path)
            return cached

        loaded = self._load_pixmap(path)
        if loaded is None:
            return self._placeholder

        self._cache[path] = loaded
        if len(self._cache) > self._max_items:
            self._cache.popitem(last=False)
        return loaded

    def _load_pixmap(self, image_path: str) -> Optional[QPixmap]:
        """按目标尺寸解码图像，避免先全尺寸解码再缩放。"""
        path = Path(image_path)
        if not path.exists():
            return None

        reader = QImageReader(str(path))
        if not reader.canRead():
            return None
        reader.setAutoTransform(True)
        reader.setScaledSize(self._thumbnail_size)
        image = reader.read()
        if image.isNull():
            return None

        return QPixmap.fromImage(image)

    def _build_placeholder(self) -> QPixmap:
        """构建浅色占位图，避免空白闪烁。"""
        width = max(48, self._thumbnail_size.width())
        height = max(32, self._thumbnail_size.height())
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#EEF2F8"))

        painter = QPainter(pixmap)
        painter.setPen(QColor("#98A2B3"))
        painter.drawText(pixmap.rect(), int(Qt.AlignCenter), "加载中")
        painter.end()
        return pixmap
