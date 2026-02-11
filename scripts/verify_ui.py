"""
UI 快速验证脚本

用于快速验证 PyQt5 UI 基础功能是否正常。

使用方法:
    python scripts/verify_ui.py

Author: haneball17
Date: 2026-02-11
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    print("✅ PyQt5 导入成功")
except ImportError as e:
    print(f"❌ PyQt5 导入失败: {e}")
    print("\n请先安装 PyQt5:")
    print("  pip install PyQt5")
    sys.exit(1)

try:
    from ui.main_window import MainWindow
    print("✅ MainWindow 导入成功")
except ImportError as e:
    print(f"❌ MainWindow 导入失败: {e}")
    sys.exit(1)

def main():
    """主函数"""
    # 启用高 DPI 缩放
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("AradVision")
    app.setApplicationVersion("0.1.3")
    app.setOrganizationName("AradVision")

    print("\n" + "="*60)
    print("AradVision UI 验证程序")
    print("="*60)
    print("\n✅ UI 组件加载成功！")
    print("\n请按照测试指南进行以下测试：")
    print("\n【阶段 1: UI 基础功能测试】")
    print("\n测试清单:")
    print("  1. ✓ 窗口正常打开")
    print("  2. ✓ 标签页切换正常（实时监控、参数配置、系统日志、关于）")
    print("  3. ✓ 滑块拖动流畅（FPS、Y容差、攻击范围等）")
    print("  4. ✓ 技能列表可拖拽排序")
    print("  5. ✓ 添加/删除技能功能正常")
    print("  6. ✓ 下拉框选择正常（显示器、模式、级别、主题）")
    print("  7. ✓ 复选框点击响应正常")
    print("  8. ✓ 按钮点击有响应（应用、重置、保存等）")
    print("  9. ✓ 菜单栏展开正常")
    print(" 10. ✓ 快捷键显示正确（F5、F12）")
    print(" 11. ✓ 日志面板等宽字体显示")
    print(" 12. ✓ 状态面板各组件显示完整")
    print(" 13. ✓ 关于页面信息正确")
    print("\n详细测试指南请参考: docs/PyQt5-UI测试指南.md")
    print("\n" + "="*60)
    print("开始测试...")
    print("="*60 + "\n")

    # 创建主窗口
    window = MainWindow()

    # 显示窗口
    window.show()

    # 进入事件循环
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
