# WGC窗口级捕获改造

- 文档主题：WGC窗口级捕获改造
- 文档路径：`docs/WGC窗口级捕获改造/WGC窗口级捕获改造.md`
- 编写日期：2026-02-18
- 角色：架构与逻辑工程师（Codex）

## 1. 背景与问题定义

当前项目的捕获链路基于 `MSS + 窗口矩形区域截屏`，本质是抓取桌面最终合成画面：
- 先通过窗口标题获取 `hwnd`
- 再通过 `GetWindowRect` 获取捕获区域
- 最后调用 `mss.grab(monitor_rect)` 抓取屏幕区域

这会导致一个关键问题：
- 若目标游戏窗口被其他窗口遮挡，返回的是上层窗口图像，而不是目标游戏窗口自身图像。

该问题会直接影响检测准确性与自动化稳定性，因此需要引入真正的“窗口级捕获”后端。

## 2. 改造目标

### 2.1 核心目标

1. 在 Windows 平台新增 WGC（Windows Graphics Capture）后端，按窗口句柄捕获目标窗口内容。  
2. 保持现有引擎接口稳定，业务主循环无感切换。  
3. 支持后端选择与自动降级机制，确保可运行性。

### 2.2 预期效果

- 游戏窗口被遮挡时，优先返回目标窗口内容（而非上层窗口内容）。
- 当 WGC 环境不满足时自动降级到 MSS，不阻断主流程。

## 3. 范围与非目标

### 3.1 本次范围

- `core/capture.py` 捕获后端抽象与 WGC 后端实现
- `core/config.py` 捕获后端配置接入
- `configs/config.yaml` 新配置项示例
- `main.py` / `ui/threads/engine_thread.py` 后端配置透传
- 对应测试与验证脚本

### 3.2 非目标

- 本次不重构检测算法与状态机策略
- 本次不引入跨平台（Linux/macOS）窗口级捕获实现
- 本次不承诺覆盖独占全屏 + 强反作弊的全部场景

## 4. 设计方案

### 4.1 架构策略

在保持 `CaptureEngine` 外部调用方式不变的前提下，引入后端分层：

- `MSSCaptureBackend`：保留现有桌面区域截屏能力
- `WGCCaptureBackend`：新增窗口级捕获能力
- `create_capture_engine(...)`：根据配置选择后端，失败则降级

目标是让上层模块继续只关心：
- `start()`
- `get_frame()`
- `stop()`
- `get_stats()`

### 4.2 配置设计

在 `capture` 配置块新增：

- `backend: auto | wgc | mss`
  - `auto`：优先 WGC，失败降级 MSS
  - `wgc`：强制尝试 WGC，失败可按策略报错或降级（建议降级并告警）
  - `mss`：强制使用现有路径

可选扩展项（按实现情况启用）：
- `wgc_show_cursor: bool`
- `wgc_force_borderless: bool`

### 4.3 兼容与降级策略

- 平台不是 Windows：直接使用 MSS。
- WGC 依赖缺失 / 初始化失败：记录警告并回退 MSS。
- 目标窗口句柄失效：尝试重新查找；连续失败后回退或抛出捕获异常。

## 5. 代码改动清单（计划）

### 5.1 核心模块

1. `core/capture.py`
- 新增捕获后端抽象
- 拆分现有 MSS 逻辑为独立后端类
- 新增 WGC 后端类
- 统一统计信息更新与异常处理

2. `core/config.py`
- 扩展 `CaptureConfig` 数据模型字段（`backend` 等）
- 更新解析逻辑与默认配置生成逻辑
- 增加配置校验（非法 backend 值）

3. `configs/config.yaml`
- 新增 `capture.backend` 示例与注释

### 5.2 调用侧

4. `main.py`
- 初始化捕获引擎时读取并透传后端配置
- 启动日志打印“请求后端 / 实际后端 / 降级信息”

5. `ui/threads/engine_thread.py`
- 与主程序保持一致的捕获后端选择逻辑

### 5.3 测试与脚本

6. `tests/test_capture_factory.py`（新增）
- 覆盖后端选择/降级路径

7. `tests/test_config_capture_backend.py`（新增）
- 覆盖配置解析、默认值、非法值

8. `scripts/verify_capture_backend.py`（新增）
- 人工验证脚本：窗口遮挡前后帧源对比

## 6. 分阶段实施计划

### 阶段 A：重构现有捕获模块（低风险）

- 抽离 MSS 后端，保证行为不变
- 编译与基础测试通过

### 阶段 B：接入 WGC 后端（核心）

- 完成 WGC 初始化、帧获取、资源释放
- 实现异常与降级路径

### 阶段 C：配置与调用侧打通（联调）

- 配置项生效
- 主线程 / UI 线程一致行为

### 阶段 D：验证与文档收尾

- 自动化测试 + 手工遮挡验证
- 输出工作总结与回滚说明

## 7. 风险评估

1. WGC 依赖与系统版本限制（Windows 10/11 可用性差异）
- 缓解：保留 MSS 兜底

2. 独占全屏或特殊渲染路径下兼容性不稳定
- 缓解：提供强制 MSS 开关

3. 引入新依赖导致部署复杂度上升
- 缓解：将 WGC 依赖放入 `requirements-full.txt`，基础环境不强依赖

## 8. 验收标准

1. 当 `capture.backend=auto/wgc` 且环境支持时，遮挡场景下仍能获取目标窗口内容。  
2. 当 WGC 不可用时，程序自动回退 MSS 且主流程不中断。  
3. `main.py` 与 UI 线程在后端选择策略上行为一致。  
4. 新增配置项解析正确、非法值可被拦截。  
5. 相关测试与脚本可用于复验。

## 9. 回滚策略

- 配置层回滚：设置 `capture.backend: mss`
- 代码层回滚：保持 `MSSCaptureBackend` 为稳定默认路径

## 10. 文档归档约定（本主题）

本次改造相关文档统一放置于：
- `docs/WGC窗口级捕获改造/`

后续建议在该目录新增：
- `实施记录.md`
- `测试记录.md`
- `工作总结_YYYY-MM-DD.md`

## 11. 实施产物索引（已落地）

- 方案文档：`docs/WGC窗口级捕获改造/WGC窗口级捕获改造.md`
- 实施记录：`docs/WGC窗口级捕获改造/实施记录.md`
- 测试记录：`docs/WGC窗口级捕获改造/测试记录.md`
- 人工验证脚本：`scripts/verify_capture_backend.py`
