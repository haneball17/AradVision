"""
数据集分析脚本 - 分析已收集的图片数据

Author: Dev A
Date: Day 1-2
"""

import cv2
from pathlib import Path
import numpy as np
from collections import Counter

class DatasetAnalyzer:
    """数据集分析工具"""

    def __init__(self, data_dir: str = "assets/images/raw"):
        self.data_dir = Path(data_dir)

    def analyze(self):
        """分析数据集"""
        if not self.data_dir.exists():
            print(f"❌ 数据目录不存在: {self.data_dir}")
            return

        # 统计各类别图片数量
        category_counts = Counter()
        total_size = 0
        resolutions = []

        print("📊 数据集分析报告")
        print("=" * 60)

        for category_dir in self.data_dir.iterdir():
            if category_dir.is_dir():
                images = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.png"))
                count = len(images)
                category_counts[category_dir.name] = count

                # 统计分辨率
                for img_path in images[:10]:  # 只检查前10张
                    img = cv2.imread(str(img_path))
                    if img is not None:
                        h, w = img.shape[:2]
                        resolutions.append((w, h))
                        total_size += img_path.stat().st_size

        # 打印统计结果
        total_images = sum(category_counts.values())

        print(f"总图片数: {total_images}")
        print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
        print()

        print("分类统计:")
        for category, count in category_counts.most_common():
            bar = "█" * int(count / max(category_counts.values()) * 30)
            print(f"  {category:12s}: {count:4d} {bar}")

        print()

        if resolutions:
            # 统计最常见的分辨率
            res_counter = Counter(resolutions)
            common_res = res_counter.most_common(1)[0][0]
            print(f"常见分辨率: {common_res[0]}x{common_res[1]}")

        print()

        # 检查是否需要更多数据
        if total_images < 100:
            print("⚠️  警告: 数据量偏少，建议至少收集 200+ 张图片")
        elif total_images < 300:
            print("⚠️  提示: 数据量适中，更多数据能提升模型效果")
        else:
            print("✅ 数据量充足")

if __name__ == "__main__":
    analyzer = DatasetAnalyzer()
    analyzer.analyze()
