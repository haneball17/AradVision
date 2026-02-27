# game-all

## 项目简介

`game-all` 是一个用于**内部授权测试**的 Windows x86 工程，整合了“游戏辅助（Helper）”与“同步器（Sync）”两套核心逻辑，并提供统一的注入器与可视化管理界面。

核心目标：
- 统一工程与构建流程（x86 + net8.0-windows）。
- 统一共享内存协议与日志输出。
- 提供稳定的注入、状态检测与模块管理能力。

> 注意：本项目仅用于内部授权环境测试。

---

## 组件概览

### 1) Payload（game-payload.dll）
- C++ x86 DLL，包含：
  - `Helper`：辅助功能与共享内存状态通道
  - `Sync`：输入同步与键盘状态共享
- 采用 MinHook 进行输入链路 Hook。
- 注入成功后写入 **successfile**（默认 `logs` 目录）。
- 进程退出时自动清理 successfile。

### 2) Injector（game-injector.exe）
- C++ x86 控制台注入器，仅使用 **APC 注入**。
- 注入结果判定：
  - **successfile 为主**
  - **共享内存心跳为兜底**
- 支持常驻监听与多进程注入：
  - `watch_mode=true` 时循环监控进程
  - `idle_exit_seconds` 无新进程出现自动退出

### 3) MasterGUI（game-master.exe）
- C# WPF（net8.0-windows）主界面，包含两个模块页：Helper / Sync
- “半集成”模式：**只提供状态展示与快捷入口**，不直接执行注入逻辑
- 通过共享内存检测注入状态与心跳

---

## 目录结构（精简）

```
./
├── GUI/                  # MasterGUI 与模块 UI
├── Injector/             # 注入器工程
├── Payload/              # DLL 工程（Helper + Sync）
├── Shared/Protocols/     # 共享协议单一来源
├── artifacts/            # 构建输出与运行目录
│   ├── bin/              # 各项目原始输出
│   ├── obj/              # 中间文件
│   └── run/              # 统一运行目录（PostBuild 复制）
│       ├── game-master.exe
│       ├── game-injector.exe
│       ├── game-payload.dll
│       └── config/       # 运行配置
├── config-templates/     # 配置模板（构建后复制到 artifacts/run/config）
├── docs/                 # 工程合并与设计文档
└── game-all.sln
```

---

## 构建前置条件

- Windows 10/11
- Visual Studio（含 C++ 桌面工作负载）
- .NET 8 Desktop Runtime
- 解决方案平台：**x86**

### MinHook 依赖
Payload 依赖 MinHook，支持以下路径：
- 头文件：
  - `Payload/lib/minhook/include/MinHook.h`
  - `Payload/lib/minhook/build/VC17/include/MinHook.h`
- 库文件：
  - `Payload/lib/minhook/lib/libMinHook.x86.lib`
  - `Payload/lib/minhook/build/VC17/lib/Release/libMinHook.x86.lib`

生成 MinHook（示例）：
1. 打开 `Payload/lib/minhook/build/VC17/MinHookVC17.sln`
2. 配置 `Win32` + `Release`
3. 构建 `libMinHook`

---

## 构建与运行

### 构建
1. 打开 `game-all.sln`
2. 平台选择 `x86`
3. 依次构建 Payload / Injector / MasterGUI

### 输出目录
- 原始输出：`artifacts/bin/...`
- 统一运行目录：`artifacts/run/`

> PostBuild 会自动复制产物到 `artifacts/run/`，并把配置模板复制到 `artifacts/run/config/`。

### 运行建议
1. 打开 `artifacts/run/` 目录
2. 启动 `game-master.exe`（可查看状态与打开注入器目录）
3. 启动 `game-injector.exe`（常驻监听并自动注入）

---

## 配置说明（运行目录）

配置文件默认位于：
```
artifacts/run/config/
```

### 1) `injector.ini`
注入器配置，关键参数：
- `process_name`：目标进程名
- `dll_path`：DLL 路径（默认 `game-payload.dll`，相对注入器输出目录）
- `window_wait_timeout_ms`：等待窗口出现的超时
- `window_poll_interval_ms`：窗口检测轮询间隔
- `post_window_delay_ms`：窗口出现后固定等待时间
- `inject_delay_ms`：额外延迟（可选）
- `watch_mode`：常驻监听
- `idle_exit_seconds`：无新进程退出阈值
- `max_concurrent_tasks`：并发注入任务上限

### 2) `mastergui.json`
MasterGUI 配置：
- `TargetProcessNames`：目标进程名列表
- `HelperHeartbeatTimeoutMs` / `SyncHeartbeatTimeoutMs`
- `SyncMappingName` / `SyncVersion` / `SyncMappingSize`
- `InjectorProcessNames`：注入器进程名
- `RequireBothModulesForInjected`：是否要求 Helper + Sync 同时在线

### 3) `game_helper.ini`
Helper 配置（支持热更新，默认 1s 轮询）：
- 启动/功能/热键/输出/日志等参数

> **当前路径**：`artifacts/run/config/game_helper.ini`  
> Payload 与 Helper GUI 均从 `./config` 读取，并支持热更新。

### 4) `params.json`
Helper GUI 参数面板的元数据。

### 5) `sync_hotkey.ini`
Sync 热键配置（支持热更新）。  
默认热键为 **Alt + .**，可修改为如 `Ctrl+F10`。

### 6) `profiles.json`
Sync 按键方案配置（热更新）。默认路径：
```
%AppData%\DNFSyncBox\profiles.json
```
模板文件：`config-templates/profiles.json`

关键字段：
- `RepeatKeys`：需要连发的键（如 `["X"]`）
- `RepeatIntervalMs`：连发间隔（毫秒）

### 7) `payload.ini`
Payload 模块总开关（运行目录 `config` 下）：
- `EnableHelper`：是否启用 Helper 模块
- `EnableSync`：是否启用 Sync 模块

> 关闭模块后仍会写入 successfile，用于保持注入判定一致。

---

## 注入结果判定

注入成功判定策略：
1. **successfile 为主**：
   - 文件名：`successfile_<dll>_<pid>.txt`
   - 默认目录：`artifacts/run/logs/`
2. **共享内存心跳兜底**：
   - 读取 Helper 状态共享内存，验证版本与更新时间

进程退出时：
- Payload 会清理 successfile
- Injector 额外做 legacy 路径清理

---

## 内存共享架构

### 架构概览

项目使用 Windows 共享内存（Named Shared Memory）实现跨进程通信，分为两大模块：

```
┌─────────────────────────────────────────────────────────────────┐
│                      共享内存架构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │   Helper Module     │         │    Sync Module      │        │
│  │  (game-payload.dll) │         │  (game-payload.dll) │        │
│  └──────────┬──────────┘         └──────────┬──────────┘        │
│             │                                │                   │
│             │ 写入                           │ 写入               │
│             ▼                                ▼                   │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │ Helper Status (V5)  │         │ Sync State (V2)     │        │
│  │   152 bytes         │         │   1824 bytes        │        │
│  └──────────┬──────────┘         └──────────┬──────────┘        │
│             │                                │                   │
│             │ 读取                           │ 读取               │
│             ▼                                ▼                   │
│  ┌─────────────────────┐         ┌─────────────────────┐        │
│  │  MasterGUI          │         │  MasterGUI / 其他   │        │
│  │  (game-master.exe)  │         │  同步客户端         │        │
│  └─────────────────────┘         └─────────────────────┘        │
│             ▲                                ▲                   │
│             │ 写入控制                       │ 写入状态           │
│             │                                │                   │
│  ┌─────────────────────┐                                             │
│  │ Helper Control (V4) │                                             │
│  │   56 bytes          │                                             │
│  └─────────────────────┘                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 通用约束

| 属性 | 值 | 说明 |
|------|-----|------|
| 平台 | **x86** | 32 位 Windows |
| 字节序 | **小端序** | Windows 默认 |
| 对齐方式 | **Pack = 1** | 禁止自动对齐，保证跨编译器兼容 |
| 协议来源 | `Shared/Protocols/协议说明.md` | 单一真实来源 |

### 校验原则

1. **有 Size 字段的结构体**（Helper Status/Control）：必须同时校验 `Version` 与 `Size`
2. **无 Size 字段的结构体**（Sync State）：校验 `Version` + 映射区大小

---

### 通道一：Helper 状态通道（Status）

**用途**：Payload → MasterGUI，报告 Helper 模块运行状态与功能开关

#### 命名规则
```
Local\GameHelperStatus_{pid}
Global\GameHelperStatus_{pid}
```
- **Local 优先**，Global 兜底
- `{pid}` 为目标进程 ID

#### 结构体定义：HelperStatusV5

| 属性 | 值 |
|------|-----|
| Version | `5` |
| Size | `152` 字节 |

| 字段 | 类型 | 说明 |
|------|------|------|
| `Version` | uint32 | 协议版本（固定 5） |
| `Size` | uint32 | 结构体大小（固定 152） |
| `LastTickMs` | uint64 | 最后心跳时间（毫秒） |
| `Pid` | uint32 | 目标进程 PID |
| `ProcessAlive` | int32 | 进程存活标记（0/1） |
| `AutoTransparentEnabled` | int32 | 自动透明开关 |
| `FullscreenAttackTarget` | int32 | 全屏攻击目标开关 |
| `FullscreenAttackPatchOn` | int32 | 全屏攻击补丁状态 |
| `AttractMode` | int32 | 吸怪模式 |
| `AttractPositive` | int32 | 吸怪方向 |
| `GatherItemsEnabled` | int32 | 聚物开关 |
| `DamageEnabled` | int32 | 动态倍攻开关 |
| `DamageMultiplier` | int32 | 动态倍攻倍率（1~1000） |
| `InvincibleEnabled` | int32 | 怪物零伤开关 |
| `SummonEnabled` | int32 | 召唤开关 |
| `SummonLastTick` | uint64 | 召唤最后触发时间 |
| `FullscreenSkillEnabled` | int32 | 全屏技能开关 |
| `FullscreenSkillActive` | int32 | 全屏技能激活状态 |
| `FullscreenSkillHotkey` | uint32 | 全屏技能热键 |
| `HotkeyEnabled` | int32 | 热键总开关 |
| `PlayerName` | wchar_t[32] | 玩家名（UTF-16，`\0` 结尾） |

#### 校验规则
```cpp
// 读取时校验
if (status->Version == 5 && status->Size == 152) {
    // 有效数据
}
```

#### 心跳机制
- Payload 定时更新 `LastTickMs`
- MasterGUI 检查心跳超时判断模块存活
- 超时配置：`mastergui.json` → `HelperHeartbeatTimeoutMs`

---

### 通道二：Helper 控制通道（Control）

**用途**：MasterGUI → Payload，控制 Helper 模块功能开关

#### 命名规则
```
Local\GameHelperControl_{pid}
Global\GameHelperControl_{pid}
```
- **Local 优先**，Global 兜底
- `{pid}` 为目标进程 ID

#### 结构体定义：HelperControlV4

| 属性 | 值 |
|------|-----|
| Version | `4` |
| Size | `56` 字节 |

| 字段 | 类型 | 说明 |
|------|------|------|
| `Version` | uint32 | 协议版本（固定 4） |
| `Size` | uint32 | 结构体大小（固定 56） |
| `Pid` | uint32 | 目标进程 PID |
| `LastUpdateTick` | uint32 | 最近更新时间（TickCount） |
| `FullscreenAttack` | uint8 | 全屏攻击覆盖模式 |
| `FullscreenSkill` | uint8 | 全屏技能覆盖模式 |
| `AutoTransparent` | uint8 | 自动透明覆盖模式 |
| `Attract` | uint8 | 吸怪覆盖模式 |
| `HotkeyEnabled` | uint8 | 热键覆盖模式 |
| `SummonSequence` | uint32 | 召唤序列号（递增触发一次召唤） |
| `ActionSequence` | uint32 | 动作序列号（变化时才处理动作） |
| `ActionMask` | uint32 | 动作掩码（位标记以下字段是否有效） |
| `DesiredFullscreenAttack` | uint8 | 目标：全屏攻击开关（0/1） |
| `DesiredFullscreenSkill` | uint8 | 目标：全屏技能激活（0/1） |
| `DesiredAutoTransparent` | uint8 | 目标：自动透明开关（0/1） |
| `DesiredAttractEnabled` | uint8 | 目标：吸怪开关（0/1） |
| `DesiredAttractMode` | uint8 | 目标：吸怪档位（1~4，0=关闭） |
| `DesiredAttractPositive` | uint8 | 目标：吸怪方向（1=正向，0=负向） |
| `DesiredHotkeyEnabled` | uint8 | 目标：热键总开关（0/1） |
| `DesiredGatherItemsEnabled` | uint8 | 目标：聚物开关（0/1） |
| `DesiredDamageMultiplier` | uint32 | 目标：动态倍攻倍率（1~1000） |
| `DesiredDamageEnabled` | uint8 | 目标：动态倍攻开关（0/1） |
| `DesiredInvincibleEnabled` | uint8 | 目标：怪物零伤开关（0/1） |

#### 覆盖模式取值
| 值 | 名称 | 说明 |
|----|------|------|
| 0 | Follow | 跟随配置文件 |
| 1 | ForceOff | 强制关闭 |
| 2 | ForceOn | 强制开启 |

#### ActionMask 位标记
| 掩码 | 字段 |
|------|------|
| 0x01 | DesiredFullscreenAttack |
| 0x02 | DesiredFullscreenSkill |
| 0x04 | DesiredAutoTransparent |
| 0x08 | DesiredAttractEnabled |
| 0x10 | DesiredAttractMode |
| 0x20 | DesiredAttractPositive |
| 0x40 | DesiredHotkeyEnabled |
| 0x80 | DesiredGatherItemsEnabled |
| 0x100 | DesiredDamageEnabled |
| 0x200 | DesiredDamageMultiplier |
| 0x400 | DesiredInvincibleEnabled |

#### 动作处理机制
```cpp
// 仅当 ActionSequence 变化时才处理 ActionMask 对应动作
uint32 lastSeq = control->ActionSequence;
// ... 等待下次读取 ...
if (control->ActionSequence != lastSeq) {
    // 处理 ActionMask 标记的动作
}
```

---

### 通道三：Sync 键盘状态通道

**用途**：Sync 模块共享键盘状态，支持多进程同步

#### 命名规则
```
Local\DNFSyncBox.KeyboardState.V2
```
- 全局命名（无 PID），支持跨进程共享
- 配置：`mastergui.json` → `SyncMappingName`

#### 结构体定义：SharedKeyboardStateV2

| 属性 | 值 |
|------|-----|
| Version | `2` |
| Size | `1824` 字节 |

| 字段 | 类型 | 说明 |
|------|------|------|
| `Version` | uint32 | 协议版本（固定 2） |
| `Seq` | uint32 | 快照序号（奇数写入，偶数完成） |
| `Flags` | uint32 | 标志位（Paused/Clear） |
| `ActivePid` | uint32 | 当前主控 PID |
| `ProfileId` | uint32 | 方案 ID |
| `ProfileMode` | uint32 | 方案模式 |
| `LastTick` | uint64 | 心跳时间戳（TickCount64） |
| `KeyboardState` | byte[256] | 键盘状态（0x80 按下，低位为切换态） |
| `EdgeCounter` | uint32[256] | 边沿计数（按下自增） |
| `TargetMask` | byte[256] | 目标键掩码（1=同步输出） |
| `BlockMask` | byte[256] | 拦截键掩码（1=强制抬起） |

#### 内存布局
```
+------------------+
| Version (4)      |  固定 2
+------------------+
| Seq (4)          |  快照序号
+------------------+
| Flags (4)        |  标志位
+------------------+
| ActivePid (4)    |  主控进程
+------------------+
| ProfileId (4)    |  方案ID
+------------------+
| ProfileMode (4)  |  方案模式
+------------------+
| LastTick (8)     |  心跳
+------------------+
| KeyboardState (256)   ← 键盘状态数组
+------------------+
| EdgeCounter (1024)    ← 256 * uint32
+------------------+
| TargetMask (256)      ← 目标掩码
+------------------+
| BlockMask (256)       ← 拦截掩码
+------------------+
Total: 1824 bytes
```

#### 双缓冲写入机制
```cpp
// 写入流程
state->Seq = odd_number;   // 标记写入中
// ... 写入数据 ...
state->Seq = even_number;  // 标记完成
```
- 读取端仅读取 `Seq` 为偶数时的快照

---

### 命名空间策略：Local vs Global

| 命名空间 | 权限 | 用途 | 优先级 |
|----------|------|------|--------|
| `Local\` | 会话内 | 同一用户会话进程通信 | **优先** |
| `Global\` | 全局 | 跨会话/跨用户进程通信 | 兜底 |

**实现**：
```cpp
// Helper 依次尝试 Local → Global
const wchar_t* prefixes[] = { L"Local\\", L"Global\\" };
for (int i = 0; i < 2; i++) {
    swprintf(name_buffer, L"%sGameHelperStatus_%u", prefixes[i], pid);
    HANDLE mapping = CreateFileMappingW(...);
    if (mapping) break;
}
```

---

### 配置参数

#### MasterGUI 相关（`mastergui.json`）

```json
{
  "HelperHeartbeatTimeoutMs": 3000,
  "SyncHeartbeatTimeoutMs": 3000,
  "SyncMappingName": "Local\\DNFSyncBox.KeyboardState.V2",
  "SyncVersion": 2,
  "SyncMappingSize": 1824
}
```

| 参数 | 说明 |
|------|------|
| `HelperHeartbeatTimeoutMs` | Helper 心跳超时（毫秒） |
| `SyncHeartbeatTimeoutMs` | Sync 心跳超时（毫秒） |
| `SyncMappingName` | Sync 共享内存名称 |
| `SyncVersion` | Sync 协议版本 |
| `SyncMappingSize` | Sync 映射区大小（字节） |

#### Payload 环境变量

| 变量 | 说明 |
|------|------|
| `DNFSYNC_HEARTBEAT_TIMEOUT_MS` | Sync 心跳超时（毫秒） |
| `DNFSYNC_SNAPSHOT_CACHE_MS` | Sync 快照缓存时间（毫秒） |

---

### 调试建议

#### 验证共享内存状态
1. 使用 Process Explorer 查找命名内存映射
2. 搜索模式：`GameHelperStatus_*` / `GameHelperControl_*` / `DNFSyncBox*`
3. 检查 `Size` 是否与协议一致

#### 常见问题
| 症状 | 可能原因 |
|------|----------|
| MasterGUI 显示"未注入" | 共享内存未创建或版本不匹配 |
| 心跳超时 | Payload 崩溃或挂起 |
| 控制无效 | ActionSequence 未变化或 ActionMask 错误 |

---

## 日志与输出

所有运行日志统一输出到 `./logs`：
- `session.current`：本次会话标识（MasterGUI 启动生成）
- `session_<sessionId>/`：会话归档（退出时复制）
- `master/master_<sessionId>_<pid>.log`（Debug）
- `injector/injector_<sessionId>_<pid>.log`（Debug）
- `payload/payload_<sessionId>_<pid>.log`（Debug）
- `helper/helper_<sessionId>_<pid>.log.jsonl`
- `sync/gui/sync_gui_<sessionId>_<pid>.log`
- `sync/payload/sync_payload_<sessionId>_<pid>.log`

---

## 运行参数（环境变量）

Payload 相关环境变量：
- `DNFSYNC_SPOOF_DELAY_MS`：注入后伪造延迟（毫秒）
- `DNFSYNC_HEARTBEAT_TIMEOUT_MS`：共享心跳超时（毫秒）
- `DNFSYNC_SNAPSHOT_CACHE_MS`：共享快照缓存时间（毫秒）
- `DNFSYNC_RAWINPUT_LOG`：RawInput 日志开关（1/true/yes/on）
- `DNFSYNC_RAWINPUT_LOG_INTERVAL_MS`：RawInput 日志采样间隔（毫秒）
- `config/sync_debug.ini`：优先级高于环境变量的调试配置（若存在）
- `DNFSYNC_FORCE_DI_OK`：DirectInput 返回 DIERR_NOTACQUIRED 时强制 DI_OK
- `DNFSYNC_STATS`：Sync 统计日志开关（1/true/yes/on）
- `DNFSYNC_STATS_INTERVAL_MS`：统计日志输出间隔（毫秒）
- `DNFSYNC_DIAG`：Sync 诊断日志开关（1/true/yes/on）
- `DNFSYNC_DIAG_INTERVAL_MS`：诊断日志输出间隔（毫秒）
- `DNFSYNC_KEYLOG`：按键事件日志开关（1/true/yes/on）
- `DNFSYNC_KEYLOG_INTERVAL_MS`：按键事件日志采样间隔（毫秒）
- `DNFSYNC_KEYLOG_LEVEL`：按键日志级别（1=RawInput，2=含 Win32，3=含 DirectInput）
- `DNFSYNC_KEYUP_TIMEOUT_MS`：KeyUp 缺失告警阈值（毫秒）

---

## 常见问题

### 1) 注入器运行后窗口闪退
- 请确保以管理员运行
- 检查 `injector.ini` 的 `dll_path` 是否有效

### 2) successfile 不生成
- 检查 `game-payload.dll` 是否成功加载
- 确认 `logs` 目录可写

### 3) 心跳超时或“未注入”
- 确认共享内存协议版本与大小一致
- 检查目标进程是否为 x86

---

## 免责声明

本项目仅用于内部授权测试环境。禁止用于任何未授权场景。
