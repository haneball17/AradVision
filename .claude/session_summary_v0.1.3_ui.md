# 会话上下文总结 - v0.1.3 UI 实现

**生成时间**: 2026-02-11
**会话主题**: PyQt5 控制面板 UI 框架实现
**相关版本**: v0.1.3

---

## 会话意图

完成 AradVision 项目的 PyQt5 控制面板 UI 框架，从简单的前端 MVP 演进为完整的总控 UI，支持后端参数管理、实时监控、日志查看等功能。

**决策演进**:
1. 初期需求：简单的屏幕捕获测试前端
2. 用户确认：需要长期总控 UI，能管理后端参数
3. 最终决策：PyQt5 桌面应用（而非 Web）

---

## 核心设计决策

### 1. UI 框架选择：PyQt5
**理由**:
- 专业游戏工具定位（类似 OBS、WeGame）
- 原生性能，无浏览器开销
- 更好的系统集成和快捷键支持
- 长期维护优势

**放弃选项**:
- OpenCV 窗口：功能过于简单
- Web 界面：不适合专业游戏工具定位

### 2. 参数生效方式：点击应用
**用户确认**: 参数修改后点击"应用所有设置"按钮才生效

**理由**:
- 防止误操作
- 支持批量修改多个参数后统一确认
- 可撤销（恢复上次设置）
- 明确的成功/失败提示

### 3. 技能编辑器：拖拽排序
**实现**: QListWidget with InternalMove 模式

**用户体验**:
- 直观的拖拽操作
- 添加/删除技能对话框
- 键位+名称显示格式

### 4. 主题系统：暗色默认
**配色方案**:
- 背景: #2B2B2B
- 面板: #3C3C3C
- 高亮: #0078D7
- 文本: #FFFFFF

**理由**: 游戏玩家偏好暗色界面，适合长时间使用

---

## 文件修改清单

### 新增核心文件

#### 主窗口
- `ui/main_window.py` (326 行)
  - 四个标签页框架
  - 菜单栏、工具栏、状态栏
  - 快捷键绑定（F5 启动，F12 紧急停止）

#### UI 组件 (ui/widgets/)
- `video_preview.py` (119 行)
  - OpenCV BGR → RGB → QImage 转换
  - 等比例缩放保持画面质量
  - 待机状态占位文本

- `status_panel.py` (251 行)
  - 性能指标：FPS 进度条、延迟、帧数、运行时长
  - 决策状态：当前状态、持续时长、状态历史
  - 检测信息：英雄、怪物、物品、门、房间
  - 快速控制：启动/暂停/停止按钮

- `parameter_panel.py` (519 行)
  - 5 个参数组：捕获、战斗、高级、日志、UI
  - 滑块实时数值显示
  - 技能列表集成
  - 配置管理按钮（保存/加载/导出/导入/重置）

- `skill_list.py` (177 行)
  - 拖拽排序实现
  - 添加技能对话框（键位+名称输入）
  - 获取/设置技能顺序方法
  - **Bug 修复**: `setDefaultDropAction` 调用方式修正

- `log_panel.py` (343 行)
  - 日志级别过滤（DEBUG/INFO/WARNING/ERROR）
  - 关键词搜索
  - 颜色编码显示
  - 日志统计（总数+各级别计数）
  - 自动滚动开关
  - 最大 1000 行限制
  - 导出功能（HTML → 纯文本）

#### 配置和主题
- `ui/config/manager.py` (162 行)
  - YAML 配置加载/保存
  - 参数验证
  - 默认值管理

- `ui/themes/dark.qss` (151 行)
  - 完整暗色主题样式表

- `ui/themes/light.qss` (151 行)
  - 完整亮色主题样式表

#### 线程和信号
- `ui/threads/signals.py` (48 行)
  - 自定义信号定义：frame_ready, status_update, log_message, error_occurred

#### 启动脚本
- `scripts/test_pyqt_ui.py` (53 行)
  - 高 DPI 缩放启用
  - 独立 UI 启动入口
  - **Bug 修复**: Qt 属性导入修正

### 文档新增
- `docs/PyQt控制面板UI设计文档.md` (965 行)
  - 完整的 UI 设计规范和实现指南

- `docs/UI启动指南.md`
  - 用户使用说明
  - 功能详解
  - 快捷键列表
  - 故障排除

- `docs/v0.1.3工作总结.md`
  - 本版本开发总结
  - 技术亮点说明
  - 待完成功能列表

### 模块导出更新
- `ui/widgets/__init__.py`
  - 导出所有组件：VideoPreviewWidget, StatusPanel, ParameterPanel, SkillListWidget, LogPanel, LogHandler

---

## 技术实现细节

### 信号-槽架构
```python
# 线程间通信
class EngineSignals(QObject):
    frame_ready = pyqtSignal(np.ndarray)  # 30 FPS
    status_update = pyqtSignal(dict)       # 5 Hz
    log_message = pyqtSignal(str, str)     # (level, message)
    error_occurred = pyqtSignal(str)        # error message
```

### 实时数值预览模式
```python
# 滑块拖动时更新标签，但不应用参数
self.fps_slider.valueChanged.connect(
    lambda v: self.fps_value_label.setText(str(v))
)
# 点击"应用"按钮时才收集并应用参数
self.btn_apply.clicked.connect(self.apply_settings)
```

### 日志颜色编码
```python
color_map = {
    "DEBUG": "#808080",   # 灰色
    "INFO": "#4FC3F7",     # 蓝色
    "WARNING": "#FFB74D",  # 橙色
    "ERROR": "#EF5350"     # 红色
}
```

### QSS 主题结构
```css
QMainWindow { background-color: #2B2B2B; }
QGroupBox { border: 1px solid #555555; ... }
QPushButton { ... }
QPushButton:hover { ... }
QPushButton:pressed { ... }
```

---

## Bug 修复记录

### Bug 1: skill_list.py 拖放设置错误
**问题**: `setDefaultDropAction(Qt.MoveAction)` 作为全局函数调用
**修复**: 改为 `self.setDefaultDropAction(Qt.MoveAction)`
**影响**: 拖拽功能无法正常工作

### Bug 2: test_pyqt_ui.py 缺少 Qt 导入
**问题**: 直接使用 `Qt.AA_EnableHighDpiScaling` 但未导入 Qt
**修复**: 添加 `from PyQt5.QtCore import Qt`
**影响**: 高 DPI 缩放无法启用，4K 屏幕显示模糊

---

## 待实现功能（预留接口）

### 1. 引擎线程 (ui/threads/engine_thread.py)
**状态**: 未实现
**需求**:
- 将核心引擎（CaptureEngine → Detector → WorldModel → BotFSM → InputDriver）包装为 Qt 工作线程
- 通过信号与主线程通信
- 支持启动/停止/暂停控制
- 实现 F12 紧急停止（os._exit(0)）

### 2. 主题切换逻辑
**状态**: 预留接口 `apply_theme(theme: str)`
**需求**:
- 动态加载 QSS 文件
- 300ms 平滑过渡动画
- 保存主题偏好到配置文件

### 3. 配置持久化
**状态**: 预留方法（save_config, load_config, export_config, import_config）
**需求**:
- 连接 ParameterPanel 到 UIManager
- 启动时自动加载配置
- 参数修改检测并提示保存
- YAML 文件读写错误处理

### 4. 日志系统集成
**状态**: LogPanel 已实现，未连接到 loguru
**需求**:
- 配置 loguru 输出到 LogHandler
- 实时日志显示
- 日志级别过滤生效

---

## 当前状态

### ✅ 已完成
- [x] 四个标签页 UI 框架
- [x] 视频预览组件
- [x] 状态面板组件
- [x] 参数配置面板（含技能列表）
- [x] 日志面板组件
- [x] 暗色/亮色主题 QSS 文件
- [x] 信号定义
- [x] 配置管理器框架
- [x] UI 启动脚本
- [x] 完整文档

### ⚠️ 部分完成
- [~] 主窗口菜单/工具栏（已创建，部分功能未连接）
- [~] 快捷键绑定（已定义，功能未实现）

### ❌ 待实现
- [ ] 引擎线程（EngineThread）
- [ ] 主题切换逻辑
- [ ] 配置自动加载/保存
- [ ] loguru 日志集成
- [ ] F12 紧急停止实现

---

## 下一步建议

### 立即可做（不影响其他模块）
1. **测试 UI 在 Windows 环境运行**
   - 安装 PyQt5
   - 运行 `python scripts/test_pyqt_ui.py`
   - 测试所有 UI 控件

2. **实现主题切换**
   - `MainWindow.apply_theme()` 方法实现
   - QSS 文件动态加载
   - 主题偏好保存

### 需要核心模块配合
3. **实现 EngineThread**
   - 等待 yangmq17 完成 WorldModel
   - 连接完整数据流
   - 测试信号通信

4. **集成日志系统**
   - loguru 添加 LogHandler
   - 测试实时日志显示

### 后续优化
5. **配置持久化**
6. **性能优化**（大量日志时的滚动性能）
7. **国际化**（中英文切换）

---

## 关键代码路径

### 启动流程
```
scripts/test_pyqt_ui.py
  → QApplication 初始化
  → MainWindow.__init__()
    → init_ui(): 创建 4 个标签页
    → init_menu(): 创建菜单栏
    → init_toolbar(): 创建工具栏
    → init_statusbar(): 创建状态栏
    → load_settings(): 加载配置（待实现）
    → apply_theme("dark"): 应用暗色主题（待实现）
  → window.show()
  → app.exec_(): 进入事件循环
```

### 参数应用流程
```
用户调整滑块
  → valueChanged 信号
  → 更新 value_label（仅显示，不应用）
用户点击"应用所有设置"
  → apply_settings()
  → collect_params(): 收集所有控件值
  → 验证参数（待实现）
  → 发送到引擎线程（待实现）
  → QMessageBox 显示结果
```

### 日志显示流程
```
loguru logger
  → LogHandler.debug/info/warning/error
  → LogPanel.add_log(level, message)
  → 格式化 HTML（带颜色）
  → apply_filters(): 根据当前过滤条件显示
  → 自动滚动到底部（如果启用）
```

---

## 性能指标

| 指标 | 值 |
|--------|-----|
| 总代码行数 | 2,746 行 |
| Python 文件 | 11 个 |
| QSS 主题文件 | 2 个 |
| 组件数量 | 6 个主要组件 |
| 设计文档 | 965 行 |

---

## 依赖要求

```python
# requirements.txt 新增
PyQt5>=5.15.0
```

**注意**:
- PyQt5 仅在 Windows 环境 UI 测试时需要
- Linux 服务器环境不需要安装
- 其他模块（vision, core）不依赖 PyQt5

---

## 参考资料

- [PyQt5 官方文档](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Qt Style Sheets 参考](https://doc.qt.io/qt-5/stylesheet-reference.html)
- 项目设计文档: `docs/PyQt控制面板UI设计文档.md`
- 用户指南: `docs/UI启动指南.md`

---

**上下文压缩版本**: v1.0
**原始会话长度**: ~150,000 tokens
**压缩后长度**: ~4,000 tokens
**压缩比**: 97.3%
