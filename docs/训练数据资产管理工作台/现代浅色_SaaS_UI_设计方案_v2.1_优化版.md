# 🎨 现代浅色 SaaS 风 UI 设计方案 v2.1（PyQt / Widgets 适配版）
（适用于《YOLO 训练数据资产管理工作台》）

> 本文档是 **设计系统 + 工程落地规范**：既包含视觉规范（token/组件/布局/动效/可用性），也包含 PyQt（Qt Widgets）落地建议（QSS 架构、命名约定、性能注意事项）。
>
> v2.1 在 v2.0 基础上补齐：**Design Tokens 分层、可访问性、状态/动效、组件清单、QSS 最佳实践**。

---

## 0. 范围与目标

### 0.1 目标
- 让应用具备“现代浅色 SaaS 工具”观感：清晰、克制、可长时间使用。
- 在 **数据密集型（缩略图 + 表格 + 筛选器）** 场景下保持高可读性。
- 样式 **集中配置、可复用、可扩展（未来暗色/高对比）**。

### 0.2 非目标
- 不追求炫酷视觉（渐变、重阴影、大面积高饱和）。
- 不追求完全自绘控件（优先 QSS + 少量自定义绘制）。

---

## 1. 设计语言总原则

### 1.1 三句口诀
- **少边框，多留白**
- **强层级，弱装饰**
- **数据优先，交互明确**

### 1.2 数据密集型 UI 规则
- 任何信息都要有“放置理由”：**缩略图角标、列表列、工具提示**分别承担不同信息密度。
- “可筛选/可排序”比“更好看”更重要：筛选器、排序、标记状态必须一眼识别。
- 视觉层级的首要手段：**字号/字重/间距**，其次才是颜色。

---

## 2. Design Tokens（设计变量）体系

> 推荐采用 **两层或三层 token**：全局 token → alias token → component token。Fluent 2 明确强调使用 token 来承载颜色、字体、间距等而非硬编码。 citeturn0search1turn0search5

### 2.1 Token 分层（建议）
- **Global tokens（原子）**：基础色板、字号、间距、圆角、阴影等级。
- **Alias tokens（语义）**：primary / danger / surface / text 等语义映射，支持多主题切换。
- **Component tokens（组件）**：按钮/输入框/卡片等组件级变量（高度、padding、状态色）。

### 2.2 推荐 token 命名（示例）
- `color.bg.app`
- `color.bg.surface`
- `color.text.primary`
- `color.border.subtle`
- `radius.sm / md / lg`
- `space.1 / 2 / 3 / 4 / 6 / 8`
- `type.title / subtitle / body / caption`

---

## 3. 色彩系统（Light Theme）

> 说明：本方案偏“Linear/Notion”清爽风。你可以保持现有主色，但务必把**状态色与文本/边框体系**统一。

### 3.1 核心语义色（Alias）
- `color.primary.500` = `#2F6BFF`
- `color.primary.600` = `#2459D8`（hover）
- `color.primary.700` = `#1D49B2`（pressed）

- `color.success.500` = `#12B76A`
- `color.warning.500` = `#F79009`
- `color.danger.500`  = `#F04438`
- `color.info.500`    = `#2E90FA`

### 3.2 中性色（Surface / Text / Border）
- `color.bg.app`      = `#F5F7FB`
- `color.bg.surface`  = `#FFFFFF`
- `color.bg.subtle`   = `#EEF2F8`
- `color.border`      = `#E7ECF3`
- `color.text.primary`   = `#1F2430`
- `color.text.secondary` = `#5B6475`
- `color.text.muted`     = `#98A2B3`

### 3.3 可访问性（建议最低标准）
- 正文文本与背景尽量达到 WCAG AA（常见做法：深灰文本 + 非纯白背景），并为 **focus** 提供明显高对比轮廓。
- 不用“仅颜色”表达状态：**颜色 + 图标/文本**双通道。

---

## 4. 字体与排版系统（Type Scale）

Material Design 强调排版层级、行高与可读性，建议用“类型标尺”管理文本层级。 citeturn0search2

### 4.1 字体栈
```text
"Segoe UI", "PingFang SC", "Microsoft YaHei UI", sans-serif
```

### 4.2 字号层级（推荐）
| Token | 用途 | 字号 | 字重 | 行高 |
|---|---|---:|---:|---:|
| `type.title` | 页面标题 | 20 | 600 | 1.25 |
| `type.h2` | 模块标题 | 16 | 600 | 1.3 |
| `type.h3` | 区块标题 | 14 | 600 | 1.3 |
| `type.body` | 正文 | 13 | 400 | 1.4 |
| `type.caption` | 辅助/注释 | 12 | 400 | 1.4 |

---

## 5. 间距与布局（8pt Grid）

### 5.1 Spacing Scale
使用 8pt 体系（4/8/12/16/24/32）并保持全局一致。

### 5.2 容器与卡片规范
- 页面外边距：24px
- 卡片内边距：16px
- 控件间距：8px
- 模块间距：24px

卡片（Surface）规范：
- 背景：`color.bg.surface`
- 圆角：12px
- 阴影：轻（见 6.3）

---

## 6. 形状、边框与阴影

### 6.1 圆角（Radius）
- `radius.sm` = 6（输入框、缩略图）
- `radius.md` = 8（按钮、标签）
- `radius.lg` = 12（卡片）

### 6.2 边框（Border）
- 默认边框尽量弱：`1px color.border`
- 不用重边框分区：分区用背景层级 + padding

### 6.3 阴影（Elevation）
- `elev.1`: 0 1px 3px rgba(0,0,0,0.06)
- hover 可使用 `elev.2`（更轻一点即可）
> 原则：**阴影用于“浮层/悬浮/选中”**，不用于所有组件。

---

## 7. 组件规范（Component Library）

> 强烈建议建立“组件清单”，避免页面上出现“同名控件不同风格”。

### 7.1 Button（按钮）
**高度**：34px（全局统一）  
**padding**：12px 14px  
**圆角**：8px  

- Primary：背景 `primary.500`，文字白
- Secondary：白底 + `border`，hover 用 `bg.subtle`
- Danger：背景 `danger.500`（仅用于破坏性操作）

交互状态：
- hover：颜色加深 / 背景轻变化
- pressed：更深一级
- disabled：降低对比度 + 禁用交互

### 7.2 Input / ComboBox（输入框与下拉）
**高度**：32px  
**圆角**：6px  
- 默认边框：`border`
- focus：`2px primary.500` outline（或外发光）

### 7.3 Checkbox / Radio
- 选中态用 primary，同时保留勾选图形
- 文字使用 body 13px

### 7.4 Slider / Range（进度条/区间）
- 轨道：`bg.subtle`
- 已选区：`primary.500`
- thumb：白底 + primary 边框
- hover：thumb 放大（轻微）

### 7.5 Tabs / Stepper（流程导航）
- 采用 Stepper（流程条）而非传统 tab：更符合“采集→筛选→预标注→导出”线性流程。
- 当前步骤：primary 高亮 + 文本加粗
- 未完成步骤：secondary 文本色
- 已完成步骤：success 或中性色标记（不要抢主色）

### 7.6 Data Table（表格）
- 行高：36px
- header：弱背景（`bg.subtle`）
- hover 行：`bg.subtle`
- 选中行：`primary` 的非常浅 tint（避免大面积蓝）

### 7.7 Thumbnail Card（缩略图卡片：核心）
默认尺寸建议：高度 72（网格）；选中 86（轻放大）

叠加信息（建议顺序）：
- 左上：objs 数量（或 bbox 类别小徽标）
- 右上：标记状态 ⭐/❌/⚠
- 下方：blur/diff（可折叠显示）

状态表现：
- ⭐ star：primary 边框 + 小星标
- ❌ reject：灰化（opacity 0.4）+ 斜线/“rejected”角标
- ⚠ review：warning 角标 + 边框弱提示

---

## 8. 交互与动效（Motion）

动效“克制但明确”：
- hover：120ms
- selection：150ms
- 页面切换：180ms
- 自动滚动：平滑

不要使用复杂缓动；桌面工具更强调“稳”。

---

## 9. 键盘与可用性（桌面工具必备）

数据筛选页建议默认支持（并在底部状态栏提示）：
- `1` ⭐、`2` ❌、`3` ⚠、`0` 清除
- `Ctrl+F` 聚焦搜索
- `Ctrl+A` 全选
- `Ctrl+E` 导出
- `Space` 快速预览（可选）

---

## 10. Qt / PyQt 落地规范（QSS 最佳实践）

### 10.1 样式表作用域与级联
Qt 官方文档说明：可以通过 `QApplication::setStyleSheet()` 设定全局样式，或对某 widget 设定，Qt 会进行级联推导。推荐 **全局统一主题**。 citeturn0search4

**建议：**
- 主题只在应用启动时加载一次（或切换主题时整体替换）。
- 避免在每个控件上频繁 `setStyleSheet()`（维护与性能都容易失控）。

### 10.2 选择器策略（工程可维护性）
- **优先用 objectName / property 选择器** 管理变体，例如：
  - `QPushButton#PrimaryButton { ... }`
  - `QWidget[role="card"] { ... }`
- 少用“深层级选择器链”，降低解析复杂度。

### 10.3 性能注意
QSS 是强大的，但过度复杂选择器/频繁重设样式会有成本；应把 QSS 当作“架构决策”对待。 citeturn0search0turn0search4

**建议：**
- 样式表文件拆分：`tokens.qss` + `components.qss` + `pages.qss`
- 对大数据缩略图区域：尽量用 `QListView/QTableView` + delegate 绘制，减少控件数量（比 1000 个 QWidget 更稳）。

---

## 11. 主题文件结构（建议）

```text
ui/
  theme/
    tokens.light.qss
    components.qss
    pages/
      capture.qss
      curation.qss
      pseudo.qss
    theme.light.qss   # import/concat
```

---

## 12. 设计验收标准

1. 页面层级一眼可辨（标题/模块/内容）。
2. 连续使用 30 分钟不疲劳（对比度与留白合理）。
3. 关键操作 2 次视线跳转内完成（筛选→标记→导出）。
4. 主题切换/扩展不需要重写组件样式（token 驱动）。
5. 无明显系统默认控件“年代感”（统一字体/边距/圆角/hover/focus）。

---

## 13. 附：建议的 Token 清单（可直接落地）

```yaml
color:
  bg:
    app: "#F5F7FB"
    surface: "#FFFFFF"
    subtle: "#EEF2F8"
  text:
    primary: "#1F2430"
    secondary: "#5B6475"
    muted: "#98A2B3"
  border:
    subtle: "#E7ECF3"
  primary:
    500: "#2F6BFF"
    600: "#2459D8"
    700: "#1D49B2"
  success: { 500: "#12B76A" }
  warning: { 500: "#F79009" }
  danger:  { 500: "#F04438" }

radius: { sm: 6, md: 8, lg: 12 }
space:  { 1: 4, 2: 8, 3: 12, 4: 16, 6: 24, 8: 32 }
type:
  title:  { size: 20, weight: 600 }
  h2:     { size: 16, weight: 600 }
  h3:     { size: 14, weight: 600 }
  body:   { size: 13, weight: 400 }
  caption:{ size: 12, weight: 400 }
```

