"""
CoordinateMapper 功能验证脚本

用于在没有 pytest 的环境中验证 CoordinateMapper 的功能。

Author: haneball17
Date: 2026-02-11
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.types import GameObject, BBox
from vision.coordinate_mapper import CoordinateMapper


def print_header(text: str):
    """打印标题"""
    print(f"\n{'=' * 60}")
    print(f" {text}")
    print('=' * 60)


def print_test(name: str, passed: bool, detail: str = ""):
    """打印测试结果"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {name}: {status}")
    if detail and not passed:
        print(f"    → {detail}")


def verify_coordinate_mapper():
    """验证 CoordinateMapper 功能"""
    print_header("CoordinateMapper 功能验证")

    test_results = []

    # 测试 1: 初始化
    print("\n1. 初始化测试")
    try:
        mapper = CoordinateMapper(
            screen_width=1920,
            screen_height=1080,
            horizon_y=540,
            depth_scale=0.0015
        )

        assert mapper.screen_width == 1920
        assert mapper.screen_height == 1080
        assert mapper.horizon_y == 540
        assert mapper.center_x == 960
        assert mapper.depth_scale == 0.0015

        test_results.append(("初始化", True, ""))
        print_test("初始化", True)
    except Exception as e:
        test_results.append(("初始化", False, str(e)))
        print_test("初始化", False, str(e))

    # 测试 2: 深度计算
    print("\n2. 深度计算测试")
    try:
        # 地平线上的点深度为 0
        depth = mapper.calculate_depth(540)
        assert depth == 0.0, f"地平线深度应为 0，实际为 {depth}"

        # 地平线以下的点深度为正
        depth_800 = mapper.calculate_depth(800)
        expected = (800 - 540) * 0.0015
        assert abs(depth_800 - expected) < 0.0001, \
            f"深度应为 {expected}，实际为 {depth_800}"

        # 地平线以上的点深度为负
        depth_300 = mapper.calculate_depth(300)
        expected = (300 - 540) * 0.0015
        assert abs(depth_300 - expected) < 0.0001, \
            f"深度应为 {expected}，实际为 {depth_300}"
        assert depth_300 < 0, "地平线以上深度应为负"

        test_results.append(("深度计算", True, ""))
        print_test("地平线深度", True)
        print_test("正深度计算", True)
        print_test("负深度计算", True)
    except Exception as e:
        test_results.append(("深度计算", False, str(e)))
        print_test("深度计算", False, str(e))

    # 测试 3: 屏幕坐标转游戏世界坐标
    print("\n3. 坐标转换测试（屏幕 → 世界）")
    try:
        # 屏幕中心对应游戏坐标原点
        world_x, world_y = mapper.screen_to_world((960, 540))
        assert abs(world_x) < 0.01, f"中心 X 应接近 0，实际为 {world_x}"
        assert abs(world_y) < 0.01, f"中心 Y 应接近 0，实际为 {world_y}"

        # 屏幕右侧
        world_x, world_y = mapper.screen_to_world((1200, 800))
        assert world_x > 0, f"右侧 X 应为正，实际为 {world_x}"
        assert world_y > 0, f"右侧 Y 应为正，实际为 {world_y}"

        # 屏幕左侧
        world_x, world_y = mapper.screen_to_world((600, 700))
        assert world_x < 0, f"左侧 X 应为负，实际为 {world_x}"

        test_results.append(("屏幕→世界转换", True, ""))
        print_test("屏幕中心转换", True)
        print_test("屏幕右侧转换", True)
        print_test("屏幕左侧转换", True)
    except Exception as e:
        test_results.append(("屏幕→世界转换", False, str(e)))
        print_test("屏幕→世界转换", False, str(e))

    # 测试 4: 游戏世界坐标转屏幕坐标
    print("\n4. 坐标转换测试（世界 → 屏幕）")
    try:
        # 游戏坐标原点对应屏幕中心
        screen_x, screen_y = mapper.world_to_screen((0.0, 0.0))
        assert screen_x == 960, f"屏幕 X 应为 960，实际为 {screen_x}"
        assert screen_y == 540, f"屏幕 Y 应为 540，实际为 {screen_y}"

        # 正坐标
        screen_x, screen_y = mapper.world_to_screen((100.0, 50.0))
        assert screen_x > 960, f"正 X 应在中心右侧"
        assert screen_y > 540, f"正 Y 应在地平线下方"

        test_results.append(("世界→屏幕转换", True, ""))
        print_test("原点转换", True)
        print_test("正坐标转换", True)
    except Exception as e:
        test_results.append(("世界→屏幕转换", False, str(e)))
        print_test("世界→屏幕转换", False, str(e))

    # 测试 5: 往返转换
    print("\n5. 往返转换测试（屏幕 → 世界 → 屏幕）")
    try:
        original = (1200, 800)

        # 屏幕坐标 → 游戏坐标
        world_pos = mapper.screen_to_world(original)

        # 游戏坐标 → 屏幕坐标
        screen_pos = mapper.world_to_screen(world_pos)

        # 误差应小于 1 像素（整数取整误差）
        assert abs(screen_pos[0] - original[0]) <= 1, \
            f"X 轴往返误差过大：{original[0]} → {screen_pos[0]}"
        assert abs(screen_pos[1] - original[1]) <= 1, \
            f"Y 轴往返误差过大：{original[1]} → {screen_pos[1]}"

        test_results.append(("往返转换", True, ""))
        print_test("往返转换", True)
    except Exception as e:
        test_results.append(("往返转换", False, str(e)))
        print_test("往返转换", False, str(e))

    # 测试 6: Y 轴对齐判断
    print("\n6. Y 轴对齐判断测试")
    try:
        # 创建测试对象
        hero = GameObject(
            id=1,
            cls_id=1,
            cls_name="hero",
            conf=0.95,
            bbox=BBox(x1=400, y1=300, x2=500, y2=500)  # 脚底 (450, 490)
        )

        # 对齐的怪物
        monster_aligned = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=500)  # 脚底 (850, 490)
        )

        # 未对齐的怪物
        monster_misaligned = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=400, x2=900, y2=600)  # 脚底 (850, 590)
        )

        # 测试对齐误差
        error_aligned = mapper.align_y_position(hero, monster_aligned)
        assert error_aligned == 0.0, f"对齐的对象误差应为 0，实际为 {error_aligned}"

        error_misaligned = mapper.align_y_position(hero, monster_misaligned)
        assert error_misaligned == 100.0, \
            f"未对齐的对象误差应为 100，实际为 {error_misaligned}"

        # 测试对齐判断
        assert mapper.is_aligned(hero, monster_aligned, tolerance=15.0), \
            "应对齐的判断为对齐"

        assert not mapper.is_aligned(hero, monster_misaligned, tolerance=15.0), \
            "不应判断为对齐"

        test_results.append(("Y 轴对齐判断", True, ""))
        print_test("对齐误差计算", True)
        print_test("对齐判断（已对齐）", True)
        print_test("对齐判断（未对齐）", True)
    except Exception as e:
        test_results.append(("Y 轴对齐判断", False, str(e)))
        print_test("Y 轴对齐判断", False, str(e))

    # 测试 7: 距离计算
    print("\n7. 距离计算测试")
    try:
        hero = GameObject(
            id=1,
            cls_id=1,
            cls_name="hero",
            conf=0.95,
            bbox=BBox(x1=400, y1=300, x2=500, y2=500)
        )

        monster = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=300, x2=900, y2=500)
        )

        # 计算距离
        distance = mapper.calculate_distance(hero, monster)
        assert distance > 0, "距离应大于 0"
        assert 300 < distance < 500, f"距离应在合理范围内，实际为 {distance}"

        test_results.append(("距离计算", True, ""))
        print_test("距离计算", True)
    except Exception as e:
        test_results.append(("距离计算", False, str(e)))
        print_test("距离计算", False, str(e))

    # 测试 8: 攻击范围判断
    print("\n8. 攻击范围判断测试")
    try:
        hero = GameObject(
            id=1,
            cls_id=1,
            cls_name="hero",
            conf=0.95,
            bbox=BBox(x1=400, y1=300, x2=500, y2=500)  # 脚底 (450, 490)
        )

        # Y 轴对齐，X 轴较近
        monster_near = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=500, y1=300, x2=600, y2=500)  # 脚底 (550, 490)
        )

        # Y 轴未对齐
        monster_misaligned = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=480, y1=400, x2=580, y2=600)  # 脚底 (530, 590)
        )

        assert mapper.is_in_attack_range(hero, monster_near, attack_range=200.0), \
            "Y 轴对齐且在范围内应返回 True"

        assert not mapper.is_in_attack_range(hero, monster_misaligned, attack_range=200.0), \
            "Y 轴未对齐应返回 False"

        test_results.append(("攻击范围判断", True, ""))
        print_test("Y 轴对齐（在范围内）", True)
        print_test("Y 轴未对齐", True)
    except Exception as e:
        test_results.append(("攻击范围判断", False, str(e)))
        print_test("攻击范围判断", False, str(e))

    # 测试 9: 方向判断
    print("\n9. 方向判断测试")
    try:
        hero = GameObject(
            id=1,
            cls_id=1,
            cls_name="hero",
            conf=0.95,
            bbox=BBox(x1=400, y1=300, x2=500, y2=500)  # 脚底 (450, 490)
        )

        # Y 轴方向
        monster_up = GameObject(
            id=2,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=200, x2=900, y2=400)  # 脚底 (850, 390)
        )
        monster_down = GameObject(
            id=3,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=800, y1=350, x2=900, y2=550)  # 脚底 (850, 540)
        )

        assert mapper.get_y_direction(hero, monster_up) == -1, "应向上"
        assert mapper.get_y_direction(hero, monster_down) == 1, "应向下"

        # X 轴方向
        monster_left = GameObject(
            id=4,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=100, y1=300, x2=200, y2=500)  # 脚底 (150, 490)
        )
        monster_right = GameObject(
            id=5,
            cls_id=0,
            cls_name="monster",
            conf=0.85,
            bbox=BBox(x1=700, y1=300, x2=800, y2=500)  # 脚底 (750, 490)
        )

        assert mapper.get_x_direction(hero, monster_left) == -1, "应向左"
        assert mapper.get_x_direction(hero, monster_right) == 1, "应向右"

        test_results.append(("方向判断", True, ""))
        print_test("Y 轴方向（向上/向下）", True)
        print_test("X 轴方向（向左/向右）", True)
    except Exception as e:
        test_results.append(("方向判断", False, str(e)))
        print_test("方向判断", False, str(e))

    # 测试 10: 分辨率调整
    print("\n10. 分辨率调整测试")
    try:
        old_width = mapper.screen_width
        old_height = mapper.screen_height

        mapper.resize(1280, 720)

        assert mapper.screen_width == 1280, f"宽度应为 1280，实际为 {mapper.screen_width}"
        assert mapper.screen_height == 720, f"高度应为 720，实际为 {mapper.screen_height}"
        assert mapper.center_x == 640, f"中心 X 应为 640，实际为 {mapper.center_x}"
        assert mapper.horizon_y == 360, f"地平线 Y 应为 360，实际为 {mapper.horizon_y}"

        test_results.append(("分辨率调整", True, ""))
        print_test("分辨率调整", True)
    except Exception as e:
        test_results.append(("分辨率调整", False, str(e)))
        print_test("分辨率调整", False, str(e))

    # 测试 11: 获取配置信息
    print("\n11. 获取配置信息测试")
    try:
        info = mapper.get_info()

        assert isinstance(info, dict), "应返回字典"
        assert info["screen_width"] == 1280
        assert info["screen_height"] == 720
        assert info["horizon_y"] == 360
        assert info["center_x"] == 640
        assert info["depth_scale"] == 0.0015

        test_results.append(("获取配置信息", True, ""))
        print_test("获取配置信息", True)
    except Exception as e:
        test_results.append(("获取配置信息", False, str(e)))
        print_test("获取配置信息", False, str(e))

    # 统计结果
    print_header("测试结果统计")

    passed_count = sum(1 for _, passed, _ in test_results if passed)
    failed_count = len(test_results) - passed_count

    print(f"\n总计: {len(test_results)} 个测试")
    print(f"通过: {passed_count} 个 ✓")
    print(f"失败: {failed_count} 个 ✗")
    print(f"通过率: {passed_count / len(test_results) * 100:.1f}%")

    if failed_count == 0:
        print("\n✅ 所有测试通过！CoordinateMapper 功能正常。")
        return 0
    else:
        print(f"\n⚠️ 有 {failed_count} 个测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    exit_code = verify_coordinate_mapper()
    sys.exit(exit_code)
