#!/usr/bin/env python3
"""
逻辑层验证脚本

用于在没有完整依赖环境的情况下验证决策层代码的正确性。
只依赖标准库和核心数据类型，不需要安装额外的包。

Usage:
    python3 scripts/verify_logic_layer.py
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """测试模块导入"""
    print("=== 1. 模块导入测试 ===\n")
    
    modules = [
        ("core.types", "核心数据类型"),
        ("core.exceptions", "异常定义"),
        ("input.base_driver", "输入驱动基类"),
        ("input.mock_driver", "Mock输入驱动"),
        ("logic.bot_fsm", "状态机"),
        ("logic.combat", "战斗逻辑"),
        ("logic.path_planner", "路径规划"),
    ]
    
    success = 0
    for module, desc in modules:
        try:
            __import__(module)
            print(f"✓ {module:30s} # {desc}")
            success += 1
        except Exception as e:
            print(f"✗ {module:30s} # {desc}")
            print(f"  错误: {e}")
    
    print(f"\n导入测试: {success}/{len(modules)} 通过\n")
    return success == len(modules)

def test_data_types():
    """测试数据类型"""
    print("=== 2. 数据类型测试 ===\n")
    
    from core.types import (
        CommandType, BotState, ObjectType,
        BBox, GameObject, GameContext,
        PlayerState, Command
    )
    
    # 测试 BBox
    bbox = BBox(100, 200, 150, 250)
    assert bbox.width == 50, "BBox.width 计算错误"
    assert bbox.height == 50, "BBox.height 计算错误"
    assert bbox.center == (125, 225), "BBox.center 计算错误"
    print("✓ BBox 类测试通过")
    
    # 测试 GameObject
    obj = GameObject(
        id=1, cls_id=0, cls_name="monster",
        conf=0.85, bbox=bbox
    )
    assert obj.object_type == ObjectType.MONSTER, "ObjectType 映射错误"
    # foot_point 计算: cx=125, fy=int(250*0.95 + 200*0.05)=int(247.5)=247
    expected_foot = (125, 247)
    assert obj.foot_point == expected_foot, f"foot_point 计算错误: {obj.foot_point} != {expected_foot}"
    print("✓ GameObject 类测试通过")
    
    # 测试 GameContext
    context = GameContext(
        frame_index=0,
        timestamp=0.0,
        hero=obj,
        monsters=[obj],
        items=[],
        doors=[]
    )
    assert context.has_monsters, "has_monsters 应为 True"
    assert not context.has_items, "has_items 应为 False"
    print("✓ GameContext 类测试通过")
    
    # 测试 Command (兼容性)
    cmd1 = Command(action_type=CommandType.ATTACK, key_code="x")
    cmd2 = Command(cmd_type=CommandType.MOVE, direction=(1, 0))
    assert cmd1.action_type == CommandType.ATTACK, "action_type 赋值错误"
    assert cmd2.action_type == CommandType.MOVE, "cmd_type 兼容性错误"
    print("✓ Command 类测试通过（兼容性）")
    
    print()

def test_bot_fsm():
    """测试状态机"""
    print("=== 3. 状态机测试 ===\n")

    from core.types import GameContext, GameObject, BBox, CommandType, PlayerState
    from logic.bot_fsm import BotFSM, BotState

    fsm = BotFSM()

    # 测试初始状态
    assert fsm.current_state == BotState.IDLE, f"初始状态应为 IDLE，实际为 {fsm.current_state}"
    print(f"✓ 初始状态: {fsm.current_state}")

    # 创建测试上下文（有怪物）
    hero_bbox = BBox(900, 500, 960, 600)
    monster_bbox = BBox(400, 450, 450, 530)

    context = GameContext(
        frame_index=0,
        timestamp=0.0,
        hero=GameObject(id=1, cls_id=1, cls_name="hero", conf=1.0, bbox=hero_bbox),
        monsters=[GameObject(id=2, cls_id=0, cls_name="monster", conf=0.9, bbox=monster_bbox)],
        player_state=PlayerState(hp_percent=1.0)
    )

    # 测试状态转换
    command = fsm.update(context)
    print(f"✓ 状态转换: IDLE -> {fsm.current_state}")
    print(f"✓ 输出指令: {command}")

    assert fsm.current_state == BotState.COMBAT, f"有怪物时应进入 COMBAT 状态，实际为 {fsm.current_state}"

    print()

def test_combat_logic():
    """测试战斗逻辑"""
    print("=== 4. 战斗逻辑测试 ===\n")

    from core.types import GameContext, GameObject, BBox, CommandType, PlayerState
    from logic.combat import CombatLogic

    combat = CombatLogic()

    # 创建测试上下文
    hero_bbox = BBox(900, 500, 960, 600)
    monster_bbox = BBox(880, 500, 930, 580)  # 已 Y 轴对齐

    context = GameContext(
        frame_index=0,
        timestamp=0.0,
        hero=GameObject(id=1, cls_id=1, cls_name="hero", conf=1.0, bbox=hero_bbox),
        monsters=[GameObject(id=2, cls_id=0, cls_name="monster", conf=0.9, bbox=monster_bbox)],
        player_state=PlayerState(hp_percent=1.0)
    )

    # 测试战斗决策
    command = combat.decide_action(context.hero, context.monsters)
    print(f"✓ 战斗决策: {command}")

    # 测试 Y 轴对齐判断
    is_aligned = context.hero.is_y_aligned(context.monsters[0], tolerance=15)
    print(f"✓ Y 轴对齐状态: {is_aligned}")

    print()

def test_path_planner():
    """测试路径规划"""
    print("=== 5. 路径规划测试 ===\n")

    from core.types import GameObject, BBox, CommandType
    from logic.path_planner import PathPlanner

    planner = PathPlanner()

    # 创建测试对象
    hero = GameObject(id=1, cls_id=1, cls_name="hero", conf=1.0,
                     bbox=BBox(900, 500, 960, 600))
    target = GameObject(id=2, cls_id=0, cls_name="monster", conf=0.9,
                       bbox=BBox(400, 450, 450, 530))

    # 测试 Y 轴对齐判断（使用 GameObject 的方法）
    is_aligned = hero.is_y_aligned(target, tolerance=15)
    print(f"✓ Y 轴对齐检查: {is_aligned}")

    # 测试路径规划
    command = planner.plan_to_target(hero, target)
    print(f"✓ 移动指令: {command}")
    if command.direction:
        print(f"✓ 移动方向: {command.direction}")
    else:
        print(f"✓ 移动类型: {command.action_type}")

    print()

def main():
    """主测试流程"""
    print("\n" + "="*60)
    print(" AradVision 逻辑层验证脚本")
    print(" 版本: v0.1.2")
    print("="*60 + "\n")
    
    tests = [
        ("模块导入", test_imports),
        ("数据类型", test_data_types),
        ("状态机", test_bot_fsm),
        ("战斗逻辑", test_combat_logic),
        ("路径规划", test_path_planner),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is None or result:
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"✗ {name} 测试失败: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ {name} 测试异常: {e}\n")
            failed += 1
    
    print("="*60)
    print(f" 测试结果: {passed} 通过, {failed} 失败")
    print("="*60 + "\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
