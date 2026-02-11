# AradVision 控制面板 UI 设计文档

**版本**: v0.1.3
**日期**: 2026-02-11
**设计者**: haneball17
**类型**: PyQt5 桌面应用（增强版）
**主题**: 暗色主题（支持切换）

---

## 📋 文档概述

本文档详细描述 AradVision 控制面板的 UI 设计方案，包括界面布局、交互设计、参数控制和实现细节。

**设计目标**：
- 提供专业的桌面控制面板
- 实时监控系统运行状态
- 灵活控制各项参数
- 支持配置保存和加载
- 提供良好的用户体验

---

## 🏗️ 整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     AradVision 主程序                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           核心引擎线程                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │ CaptureEngine│→│WorldModel   │→│  BotFSM      │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │   │
│  │         ↓                 ↓                 ↓           │   │
│  │    捕获画面           游戏上下文          决策指令       │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Qt 信号桥接层                     │   │
│  │  • 转发帧数据        • 转发状态数据                    │   │
│  │  • 接收控制信号      • 处理参数更新                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Qt GUI 线程                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │   │
│  │  │视频预览   │  │参数面板   │  │日志输出          │   │   │
│  │  │状态显示   │  │控制按钮   │  │配置管理          │   │   │
│  │  └──────────┘  └──────────┘  └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 线程模型

```
主线程 (QApplication)
  ├── Qt GUI 线程
  │   ├── 界面渲染
  │   ├── 用户交互处理
  │   └── 定时器触发 (30 FPS)
  │
  └── 核心引擎线程 (QThread)
      ├── 截图引擎 (CaptureEngine)
      ├── 检测器 (MockYoloDetector)
      ├── 世界模型 (WorldModel)
      ├── 状态机 (BotFSM)
      └── 输入驱动 (MockInputDriver)

通信方式: Qt Signals & Slots
```

---

## 🎨 界面布局设计

### 主窗口结构

```
┌─────────────────────────────────────────────────────────────────┐
│  AradVision 控制面板                             [─][□][×]      │
├─────────────────────────────────────────────────────────────────┤
│ 菜单栏: [文件] [控制] [视图] [工具] [帮助]                          │
├─────────────────────────────────────────────────────────────────┤
│ 工具栏: [▶️启动] [⏸️暂停] [⏹️停止] [💾保存] [📂加载] [🔄刷新]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  标签页: [实时监控] [参数配置] [系统日志] [关于]                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  │              标签页内容区域                                 │ │
│  │                                                            │ │
│  │                                                            │ │
│  │                                                            │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│ 状态栏: 就绪 | FPS: -- | 状态: STOPPED | v0.1.3                │
└─────────────────────────────────────────────────────────────────┘
```

### 窗口尺寸

- **最小尺寸**: 1000 x 700
- **默认尺寸**: 1200 x 800
- **可调整大小**: 是

---

## 📑 标签页详细设计

### 标签页 1: 实时监控

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [实时监控] [参数配置] [系统日志] [关于]                          │
├──────────────────────────────┬──────────────────────────────────┤
│                              │                                  │
│  📹 实时预览                   │  📊 状态面板                      │
│  ┌────────────────────────┐  │  ┌────────────────────────────┐ │
│  │                        │  │  │  性能指标                   │ │
│  │    640 x 480           │  │  │  ━━━━━●━━━━ 30.2 FPS      │ │
│  │    实时游戏画面         │  │  │  延迟: 15.3 ms             │ │
│  │                        │  │  │  帧数: 1,234                │ │
│  │                        │  │  │  运行时长: 00:05:23          │ │
│  │                        │  │  └────────────────────────────┘ │
│  └────────────────────────┘  │                                  │
│                              │  ┌────────────────────────────┐ │
│                              │  │  决策状态                   │ │
│                              │  │  当前状态: COMBAT            │ │
│                              │  │  持续时长: 5.2 秒            │ │
│                              │  │  状态历史:                  │ │
│                              │  │  IDLE → COMBAT → LOOT       │ │
│                              │  └────────────────────────────┘ │
│                              │                                  │
│                              │  ┌────────────────────────────┐ │
│                              │  │  检测信息                   │ │
│                              │  │  👤 英雄: ✓ (已检测)        │ │
│                              │  │  👹 怪物: 3 个              │ │
│                              │  │  💎 物品: 0 个              │ │
│                              │  │  🚪 门:   1 个              │ │
│                              │  │  📦 房间: 未清空            │ │
│                              │  └────────────────────────────┘ │
│                              │                                  │
│  🎮 快速控制                  │                                  │
│  ┌────────────────────────┐  │                                  │
│  │ [▶️ 启动] [⏸️ 暂停] [⏹️ 停止]│  │                                  │
│  └────────────────────────┘  │                                  │
│                              │                                  │
└──────────────────────────────┴──────────────────────────────────┘
```

#### 组件清单

| 组件 | 类型 | 说明 |
|------|------|------|
| **视频预览区** | `QLabel` | 显示实时捕获画面（640x480） |
| **FPS 指示器** | `QProgressBar` + `QLabel` | 显示当前 FPS |
| **性能指标** | `QLabel` | 延迟、帧数、运行时长 |
| **状态显示** | `QLabel` | 当前状态、持续时长、状态历史 |
| **检测信息** | `QLabel` | 英雄、怪物、物品、门、房间状态 |
| **控制按钮** | `QPushButton` | 启动、暂停、停止 |

#### 更新频率

- **视频预览**: 30 FPS (每 33ms 更新一次)
- **性能指标**: 1 Hz (每秒更新一次)
- **状态显示**: 5 Hz (每 200ms 更新一次)
- **检测信息**: 5 Hz (每 200ms 更新一次)

---

### 标签页 2: 参数配置

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [实时监控] [参数配置] [系统日志] [关于]                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📹 捕获设置                            ⚔️ 战斗配置              │
│  ┌────────────────────────────────┐  ┌────────────────────────┐ │
│  │ 目标 FPS                       │  │ Y 轴对齐容差            │ │
│  │ ┌──────────────────────────┐   │  │ ┌──────────────────┐   │ │
│  │ │ ████████████░░░░░░░░░░  │   │  │ │ ████████░░░░░░░  │   │ │
│  │ └──────────────────────────┘   │  │ └──────────────────┘   │ │
│  │ 10                           60  │  │ 5                    50  │ │
│  │ 当前值: 30                    │  │ 当前值: 15              │ │
│  └────────────────────────────────┘  └────────────────────────┘ │
│                                                                  │
│  显示器: [主显示器 ▼]               攻击范围:                      │
│  ┌──────────────────────────┐       ┌──────────────────┐         │
│  │ ████████████░░░░░░░░░░  │       │ ████████████░░░░ │         │
│  └──────────────────────────┘       50              200        │
│  当前值: 主显示器                    当前值: 100                      │
│                                                                  │
│  检测模式: [Mock ▼]                  技能优先级 (拖拽排序):         │
│                                    ┌──────────────────────────┐ │
│                                    │ ┌───┐ ┌───┐ ┌───┐       │ │
│                                    │ │ a │ │ s │ │ d │       │ │
│                                    │ └───┘ └───┘ └───┘       │ │
│                                    │ 普攻  技能  大招        │ │
│                                    └──────────────────────────┘ │
│                                    [添加技能] [删除技能]        │
│                                                                  │
│  🔧 高级设置 (点击展开)             📊 状态检测配置                │
│  ┌────────────────────────────────┐  ┌────────────────────────┐ │
│  │ 置信度阈值                    │  │ 房间清空超时              │ │
│  │ ┌──────────────────────────┐   │  │ ┌──────────────────┐   │ │
│  │ │ ████████░░░░░░░░░░░░░░  │   │  │ │ ██████░░░░░░░░░  │   │ │
│  │ └──────────────────────────┘   │  │ └──────────────────┘   │ │
│  │ 0.1                         0.9│  │ 1秒               10秒  │ │
│  │ 当前值: 0.5                   │  │ 当前值: 2.0 秒           │ │
│  └────────────────────────────────┘  └────────────────────────┘ │
│                                                                  │
│  📋 日志配置                         🎨 界面设置                  │
│  日志级别: [INFO ▼]                 主题: [暗黑 ▼]                 │
│  日志保存: [✓] 保存到文件             开机启动: [ ]                │
│                                                                  │
│  💾 配置管理                                                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ [保存配置] [加载配置] [重置默认] [导出配置] [导入配置]        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [应用所有设置]  [恢复上次设置]                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 参数分组

**分组 1: 捕获设置**
| 参数 | 类型 | 范围 | 默认值 | 控件 |
|------|------|------|--------|------|
| 目标 FPS | 滑块 | 10-60 | 30 | `QSlider` |
| 显示器 | 下拉框 | 动态 | 主显示器 | `QComboBox` |
| 检测模式 | 下拉框 | Mock/YOLO | Mock | `QComboBox` |

**分组 2: 战斗配置**
| 参数 | 类型 | 范围 | 默认值 | 控件 |
|------|------|------|--------|------|
| Y 轴对齐容差 | 滑块 | 5-50 | 15 | `QSlider` |
| 攻击范围 | 滑块 | 50-200 | 100 | `QSlider` |
| 技能优先级 | 拖拽列表 | 自定义 | [a,s,d] | `QListWidget`+拖拽 |

**分组 3: 高级设置**
| 参数 | 类型 | 范围 | 默认值 | 控件 |
|------|------|------|--------|------|
| 置信度阈值 | 滑块 | 0.1-0.9 | 0.5 | `QSlider` |
| 房间清空超时 | 滑块 | 1-10秒 | 2.0 | `QSlider` |

**分组 4: 日志配置**
| 参数 | 类型 | 选项 | 默认值 | 控件 |
|------|------|------|--------|------|
| 日志级别 | 下拉框 | DEBUG/INFO/WARNING/ERROR | INFO | `QComboBox` |
| 日志保存 | 复选框 | - | ✓ | `QCheckBox` |

**分组 5: 界面设置**
| 参数 | 类型 | 选项 | 默认值 | 控件 |
|------|------|------|--------|------|
| 主题 | 下拉框 | 明亮/暗黑 | 暗黑 | `QComboBox` |
| 开机启动 | 复选框 | - | ✗ | `QCheckBox` |

#### 按钮功能

| 按钮 | 功能 | 确认对话框 |
|------|------|------------|
| **应用所有设置** | 应用当前修改的所有参数 | 否 |
| **恢复上次设置** | 从配置文件加载上次保存的参数 | 否 |
| **保存配置** | 保存当前参数到 YAML 文件 | 文件对话框 |
| **加载配置** | 从 YAML 文件加载参数 | 文件对话框 |
| **重置默认** | 恢复所有参数为默认值 | 确认对话框 |
| **导出配置** | 导出配置为 JSON 文件 | 文件对话框 |
| **导入配置** | 从 JSON 文件导入配置 | 文件对话框 |

---

### 标签页 3: 系统日志

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [实时监控] [参数配置] [系统日志] [关于]                          │
├─────────────────────────────────────────────────────────────────┤
│  🔍 日志过滤                                                       │
│  日志级别: [全部 ▼]  搜索: [____________] [搜索]  [清空]          │
│  自动滚动: [✓]  保存日志: [ ]                                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                             ││
│  │  2026-02-11 17:30:00 | INFO  | 系统启动完成...             ││
│  │  2026-02-11 17:30:01 | DEBUG | 捕获帧 #1...              ││
│  │  2026-02-11 17:30:01 | INFO  | 检测到 3 个对象...         ││
│  │  2026-02-11 17:30:02 | WARN  | FPS 降低到 25...           ││
│  │  2026-02-11 17:30:03 | ERROR | 捕获失败...              ││
│  │  ...                                                         ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  日志统计: 总计: 1234 条 | INFO: 800 | WARN: 50 | ERROR: 5        │
│  [复制全部] [复制选中] [导出日志]                                │
└─────────────────────────────────────────────────────────────────┘
```

#### 组件清单

| 组件 | 类型 | 说明 |
|------|------|------|
| **日志过滤** | `QComboBox` | 按级别过滤日志 |
| **搜索框** | `QLineEdit` + `QPushButton` | 搜索日志内容 |
| **清空按钮** | `QPushButton` | 清空日志显示 |
| **自动滚动** | `QCheckBox` | 新日志自动滚动到底部 |
| **保存日志** | `QCheckBox` | 是否保存到文件 |
| **日志显示区** | `QTextEdit` | 只读，支持颜色 |
| **日志统计** | `QLabel` | 各级别日志数量统计 |

#### 日志颜色方案

```python
LOG_COLORS = {
    "DEBUG":    "#808080",  # 灰色
    "INFO":     "#00FF00",  # 绿色
    "WARNING":  "#FFFF00",  # 黄色
    "ERROR":    "#FF0000",  # 红色
    "CRITICAL": "#FF00FF",  # 紫色
}
```

---

### 标签页 4: 关于

#### 布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [实时监控] [参数配置] [系统日志] [关于]                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│              ┌─────────────────────────────┐                    │
│              │                             │                    │
│              │      [Logo / 图标]           │                    │
│              │                             │                    │
│              │     AradVision              │                    │
│              │   DNF 视觉辅助自动化系统      │                    │
│              │                             │                    │
│              └─────────────────────────────┘                    │
│                                                                  │
│  版本: v0.1.3                                                    │
│  构建: 2026-02-11                                                │
│  作者: haneball17, yangmq17                                      │
│                                                                  │
│  📖 项目简介                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ AradVision 是一个基于计算机视觉的 DNF 游戏辅助工具，     │   │
│  │ 使用 YOLO 目标检测和状态机决策，实现自动化战斗和         │   │
│  │ 路径规划。                                                 │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│  🔗 链接                                                         │
│  • GitHub: https://github.com/xxx/AradVision                    │
│  • 文档: https://xxx.github.io/AradVision/                       │
│  • 问题反馈: https://github.com/xxx/AradVision/issues           │
│                                                                  │
│  📄 许可证: MIT License                                          │
│                                                                  │
│  [检查更新] [查看许可证] [访问官网]                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 主题设计

### 暗色主题（默认）

```css
/* 颜色定义 */
背景色: #2B2B2B          /* 深灰背景 */
前景色: #FFFFFF          /* 白色文字 */
面板色: #3C3C3C          /* 稍浅的面板 */
边框色: #555555          /* 边框 */
高亮色: #0078D7          /* 蓝色高亮 */
成功色: #107C10          /* 绿色 */
警告色: #FF8C00          /* 橙色 */
错误色: #C5282E          /* 红色 */

/* 组件样式 */
- 按钮悬停: 背景色 +10%
- 输入框: 背景色 #1E1E1E
- 下拉框: 背景色 #1E1E1E
- 滑块: 高亮色 #0078D7
```

### 明亮主题

```css
/* 颜色定义 */
背景色: #FFFFFF          /* 白色背景 */
前景色: #000000          /* 黑色文字 */
面板色: #F0F0F0          /* 浅灰面板 */
边框色: #CCCCCC          /* 边框 */
高亮色: #0078D7          /* 蓝色高亮 */
成功色: #107C10          /* 绿色 */
警告色: #FF8C00          /* 橙色 */
错误色: #C5282E          /* 红色 */

/* 组件样式 */
- 按钮悬停: 背景色 -10%
- 输入框: 背景色 #FFFFFF
- 下拉框: 背景色 #FFFFFF
- 滑块: 高亮色 #0078D7
```

### 主题切换

```python
# 切换时平滑过渡（300ms）
QApplication.setStyleSheet("""
    QWidget {
        background-color: #2B2B2B;
        color: #FFFFFF;
    }
    QPushButton {
        transition: background-color 300ms;
    }
""")
```

---

## 🔄 交互设计

### 用户操作流程

#### 流程 1: 启动系统

```
用户操作: 点击 [▶️ 启动] 按钮
    ↓
界面响应:
    1. 按钮变灰，显示"启动中..."
    2. 禁用其他控制按钮
    3. 切换到"实时监控"标签页
    4. 日志输出: "正在启动系统..."
    ↓
系统执行:
    1. 初始化 CaptureEngine
    2. 初始化 Detector
    3. 初始化 WorldModel
    4. 启动核心引擎线程
    ↓
界面更新:
    1. 视频预览开始更新
    2. 状态面板开始刷新
    3. [启动] → [暂停] (按钮状态切换)
    4. 启用其他控制按钮
    5. 日志输出: "系统启动完成"
```

#### 流程 2: 调整参数

```
用户操作: 拖动"目标 FPS"滑块到 60
    ↓
界面响应:
    1. 实时显示当前值: "60"
    2. 滑块下方数值更新
    ↓
系统状态:
    - 参数标记为"已修改"（未生效）
    - [应用所有设置] 按钮高亮提示
    ↓
用户操作: 点击 [应用所有设置]
    ↓
系统执行:
    1. 弹出确认对话框: "应用新设置？"
    2. 用户点击 [是]
    3. 验证参数有效性
    4. 更新到核心引擎
    5. 日志输出: "参数已更新"
    6. "已修改"标记清除
```

#### 流程 3: 技能优先级编辑

```
用户操作: 拖拽技能项调整顺序
    ↓
交互细节:
    1. 鼠标悬停: 显示拖拽光标
    2. 按下左键: 技能项高亮
    3. 拖动: 显示插入位置指示器
    4. 释放: 技能项动画移动到新位置
    5. 顺序更新: 内部列表同步更新
    ↓
系统状态:
    - 参数标记为"已修改"
    - [应用所有设置] 按钮高亮
```

#### 流程 4: 保存配置

```
用户操作: 点击 [保存配置]
    ↓
系统响应:
    1. 弹出文件保存对话框
    2. 默认文件名: config_20260211_173000.yaml
    3. 默认路径: configs/
    ↓
用户操作: 选择路径，点击 [保存]
    ↓
系统执行:
    1. 验证参数有效性
    2. 序列化为 YAML 格式
    3. 写入文件
    4. 弹出提示框: "配置已保存"
    5. 日志输出: "配置已保存到 xxx.yaml"
```

#### 流程 5: 主题切换

```
用户操作: 主题下拉框选择"明亮"
    ↓
界面响应:
    1. 平滑过渡动画 (300ms)
    2. 背景色: #2B2B2B → #FFFFFF
    3. 前景色: #FFFFFF → #000000
    4. 所有组件颜色同步更新
    5. 滑块、按钮、边框等重新着色
    ↓
系统执行:
    1. 更新 QStyleSheet
    2. 保存主题设置到配置文件
    3. 下次启动自动加载
```

---

## 🛠️ 技术实现

### 核心类设计

#### MainWindow 类

```python
class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AradVision 控制面板")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # 核心组件
        self.engine_thread = None
        self.config_manager = ConfigManager()

        # UI 组件
        self.video_preview = VideoPreviewWidget()
        self.status_panel = StatusPanel()
        self.param_panel = ParameterPanel()
        self.log_panel = LogPanel()

        # 初始化
        self.init_ui()
        self.init_menu()
        self.init_toolbar()
        self.init_statusbar()
        self.apply_theme("dark")  # 默认暗色主题
```

#### VideoPreviewWidget 类

```python
class VideoPreviewWidget(QLabel):
    """视频预览组件"""

    def __init__(self):
        super().__init__()
        self.setFixedSize(640, 480)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("border: 2px solid #555555;")
        self.setPlaceholderText("等待系统启动...")

    def update_frame(self, frame: np.ndarray):
        """更新帧显示"""
        # 转换 OpenCV 图像到 QImage
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # 缩放到组件大小
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)
```

#### ParameterPanel 类

```python
class ParameterPanel(QWidget):
    """参数配置面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.params = {}  # 存储当前参数
        self.modified = False  # 是否有未保存的修改

        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()

        # 捕获设置组
        capture_group = self.create_capture_group()
        layout.addWidget(capture_group)

        # 战斗配置组
        combat_group = self.create_combat_group()
        layout.addWidget(combat_group)

        # 高级设置组
        advanced_group = self.create_advanced_group()
        layout.addWidget(advanced_group)

        # 日志配置组
        log_group = self.create_log_group()
        layout.addWidget(log_group)

        # 界面设置组
        ui_group = self.create_ui_group()
        layout.addWidget(ui_group)

        # 配置管理按钮
        config_buttons = self.create_config_buttons()
        layout.addWidget(config_buttons)

        # 应用按钮
        apply_buttons = QHBoxLayout()
        self.btn_apply = QPushButton("应用所有设置")
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_reset = QPushButton("恢复上次设置")
        self.btn_reset.clicked.connect(self.reset_settings)
        apply_buttons.addWidget(self.btn_apply)
        apply_buttons.addWidget(self.btn_reset)
        layout.addLayout(apply_buttons)

        layout.addStretch()
        self.setLayout(layout)
```

#### SkillListWidget 类

```python
class SkillListWidget(QListWidget):
    """技能优先级列表（支持拖拽）"""

    def __init__(self):
        super().__init__()
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)

        # 添加示例技能
        self.add_skill("a", "普通攻击")
        self.add_skill("s", "技能")
        self.add_skill("d", "大招")

    def add_skill(self, key, name):
        """添加技能项"""
        item = QListWidgetItem(f"{key} - {name}")
        item.setData(Qt.UserRole, key)
        self.addItem(item)

    def get_skill_order(self) -> list:
        """获取当前技能顺序"""
        order = []
        for i in range(self.count()):
            item = self.item(i)
            key = item.data(Qt.UserRole)
            order.append(key)
        return order
```

### 信号桥接设计

```python
class EngineSignals(QObject):
    """引擎信号类"""

    # 帧信号 (30 FPS)
    frame_ready = Signal(np.ndarray)

    # 状态信号 (5 Hz)
    status_update = Signal(dict)

    # 日志信号
    log_message = Signal(str, str)  # (level, message)

    # 错误信号
    error_occurred = Signal(str)


class EngineThread(QThread):
    """引擎线程"""

    def __init__(self):
        super().__init__()
        self.signals = EngineSignals()
        self.running = False
        self.paused = False

        # 核心组件
        self.capture_engine = None
        self.detector = None
        self.world_model = None
        self.fsm = None

    def run(self):
        """线程主循环"""
        while self.running:
            if not self.paused:
                # 1. 捕获帧
                frame = self.capture_engine.get_frame()
                if frame is not None:
                    # 发送帧信号
                    self.signals.frame_ready.emit(frame)

                # 2. 更新状态
                status = self.get_status()
                self.signals.status_update.emit(status)

            # 控制帧率
            msleep(33)

    def update_params(self, params: dict):
        """更新参数"""
        # 应用新参数到各个组件
        if "target_fps" in params:
            self.capture_engine.set_target_fps(params["target_fps"])
        # ... 其他参数
```

### 配置管理设计

```python
class ConfigManager:
    """配置管理器"""

    def __init__(self):
        self.config_file = "configs/config.yaml"
        self.ui_config_file = "configs/ui_config.yaml"

    def save_config(self, params: dict) -> bool:
        """保存配置到 YAML"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(params, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def load_config(self) -> dict:
        """从 YAML 加载配置"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("配置文件不存在，使用默认配置")
            return self.get_default_config()

    def get_default_config(self) -> dict:
        """获取默认配置"""
        return {
            "capture": {
                "target_fps": 30,
                "monitor_index": 0,
                "window_title": "地下城与勇士"
            },
            "detector": {
                "mode": "mock",
                "conf_threshold": 0.5,
                "iou_threshold": 0.45
            },
            "combat": {
                "y_tolerance": 15,
                "attack_range": 100,
                "skill_priority": ["a", "s", "d"]
            },
            "world_model": {
                "room_clear_timeout": 2.0
            },
            "ui": {
                "theme": "dark",
                "log_level": "INFO",
                "save_log": True
            }
        }
```

---

## 📊 数据流设计

### 界面更新数据流

```
核心引擎线程 (30 FPS)
    ↓
frame_ready 信号
    ↓
MainWindow 接收
    ↓
VideoPreviewWidget.update_frame()
    ↓
QImage 显示
```

### 状态更新数据流

```
核心引擎线程 (5 Hz)
    ↓
status_update 信号
    ↓
MainWindow 接收
    ↓
StatusPanel.update_status()
    ↓
QLabel 更新显示
```

### 参数控制数据流

```
用户操作 (拖动滑块)
    ↓
ParameterPanel 记录参数值
    ↓
用户点击 [应用所有设置]
    ↓
ParameterPanel.collect_params()
    ↓
ConfigManager.validate_params()
    ↓
EngineThread.update_params()
    ↓
核心引擎更新
```

---

## 🎯 实现优先级

### P0 - 核心功能（必须）

1. ✅ 主窗口框架
2. ✅ 标签页布局（4个标签页）
3. ✅ 实时监控标签页
   - 视频预览
   - 状态面板
   - 控制按钮
4. ✅ 参数配置标签页
   - 捕获设置
   - 战斗配置
   - 应用按钮
5. ✅ 引擎线程封装
6. ✅ 信号桥接机制

### P1 - 重要功能（增强）

7. ✅ 系统日志标签页
8. ✅ 关于标签页
9. ✅ 菜单栏
10. ✅ 工具栏
11. ✅ 状态栏
12. ✅ 配置保存/加载
13. ✅ 主题切换（明亮/暗黑）
14. ✅ 技能拖拽排序

### P2 - 可选功能（完善）

15. ⭐ 日志过滤和搜索
16. ⭐ 快捷键支持
17. ⭐ 配置导入/导出
18. ⭐ 日志导出
19. ⭐ 开机启动
20. ⭐ 检查更新

---

## 📝 附录

### 依赖清单

```
PyQt5>=5.15.0
PyQt5-sip>=12.0.0
opencv-python>=4.8.0
numpy>=1.24.0
PyYAML>=6.0.0
loguru>=0.7.0
```

### 文件结构

```
ui/
├── __init__.py
├── main_window.py      # 主窗口
├── widgets/             # 自定义组件
│   ├── video_preview.py       # 视频预览
│   ├── status_panel.py        # 状态面板
│   ├── parameter_panel.py      # 参数面板
│   ├── skill_list.py           # 技能列表
│   └── log_panel.py            # 日志面板
├── threads/             # 线程封装
│   ├── engine_thread.py        # 引擎线程
│   └── signals.py              # 信号定义
├── themes/              # 主题样式
│   ├── dark.qss                # 暗色主题
│   └── light.qss               # 明亮主题
└── config/              # 配置管理
    └── manager.py              # 配置管理器
```

### 开发时间估算

| 阶段 | 任务 | 时间 |
|------|------|------|
| **阶段 1** | 搭建框架、主窗口、标签页 | 1小时 |
| **阶段 2** | 实时监控页（视频预览、状态面板） | 1小时 |
| **阶段 3** | 参数配置页（滑块、下拉框、技能列表） | 1小时 |
| **阶段 4** | 引程线程、信号桥接、参数控制 | 1小时 |
| **阶段 5** | 系统日志页、关于页 | 30分钟 |
| **阶段 6** | 菜单栏、工具栏、状态栏 | 30分钟 |
| **阶段 7** | 主题切换、配置管理 | 30分钟 |
| **阶段 8** | 测试、调试、优化 | 1小时 |
| **总计** | | **约 6-7 小时** |

---

**文档版本**: v1.0
**最后更新**: 2026-02-11
**下一步**: 开始实现代码
