# 工作总结：AttachThreadInput 判定与诊断修复

**日期**: 2026-02-13  
**角色**: 架构与逻辑工程师（yangmq17）  
**分支**: dev  
**类型**: 输入模块缺陷修复

## 背景
在 `scripts/test_input_game.py` 的真实环境测试中，日志持续显示 `AttachThreadInput 返回 None` 并被判定为失败，导致窗口激活流程错误进入备用分支，且无法输出有效失败原因。

## 本次改动
1. 修复 `input/input_driver.py` 中 `AttachThreadInput` 的成功判定逻辑：
   - 从“依赖返回值 truthy”改为“无异常即成功”。
   - 兼容 pywin32 成功返回 `None` 的行为。
2. 增强失败诊断日志：
   - 输出异常的 `winerror`、`funcname`、`strerror`。
   - 保留 `GetLastError()` 的辅助日志。
3. 修复线程分离时机：
   - 在激活流程 `finally` 中执行线程分离，避免附加状态残留。
4. 调整激活顺序：
   - 激活前先恢复并显示窗口（`SW_RESTORE`/`SW_SHOW`），再执行前台切换与复核。

## 验证记录
1. 语法检查：`python3 -m compileall input/input_driver.py`（通过）。
2. 单元测试：当前环境未安装 `pytest`（系统 Python 与 `.venv` 均提示 `No module named pytest`），本次未执行。

## 风险与后续建议
1. 需要在 Windows 真机上复测 `scripts/test_input_game.py`，确认日志进入“AttachThreadInput 调用成功（pywin32 成功时返回 None）”分支。
2. 若仍失败，基于新增的 `winerror` 定位是否为权限/UIPI 或前台锁策略限制。
