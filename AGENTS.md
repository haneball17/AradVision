# Repository Guidelines

## Project Structure & Module Organization
AradVision is a Python project organized by domain modules:
- `core/`: shared infrastructure (config, logging, capture, types, exceptions).
- `vision/`: detection interfaces and mock detector.
- `logic/`: decision-making (`bot_fsm.py`, `combat.py`, `path_planner.py`).
- `input/`: real/mock input drivers and kill switch.
- `tests/`: unit tests (`tests/test_*.py`) and integration tests (`tests/integration/`).
- `configs/`: runtime YAML config (`configs/config.yaml`).
- `scripts/`: project/bootstrap/data helper scripts.
- `main.py`: application entry point.

## Build, Test, and Development Commands
- `python3 -m venv .venv && source .venv/bin/activate`: create and activate a local environment.
- `pip install -r requirements.txt`: install dependencies.
- `python3 main.py -c configs/config.yaml`: run the app with explicit config.
- `python3 -m pytest -q`: run all tests.
- `python3 -m pytest tests/integration/test_full_flow_mock.py -q`: run key integration flow.
- `python3 -m compileall core input logic vision tests`: quick syntax validation.

## Coding Style & Naming Conventions
- Follow PEP 8 with **4-space indentation** and **max line length 100**.
- Type hints are required for function parameters and return values.
- Naming: `snake_case` (modules/functions/variables), `PascalCase` (classes), `UPPER_CASE` (constants).
- Use `core/logger.py` (loguru) for logs; do not use `print()` for runtime diagnostics.
- Keep thresholds, key mappings, and tunables in `configs/config.yaml` (no magic numbers).
- Project convention requires clear Chinese comments/docstrings for non-trivial logic.

## Testing Guidelines
- Framework: `pytest`.
- Test files must be named `test_*.py`; keep fixtures in `tests/conftest.py`.
- Add unit tests for new logic branches and integration tests for cross-module flows.
- Before merge, run focused tests for changed modules, then run full test suite.

## Commit & Pull Request Guidelines
- Prefer Conventional Commit prefixes seen in history: `feat`, `fix`, `docs`, `chore` (optionally with scope, e.g., `feat(yangmq17): ...`).
- Keep commits focused and atomic; include related test updates in the same commit.
- Git commit summaries/descriptions must be written in Chinese and include the contributor role (e.g., `角色: 架构与逻辑工程师（yangmq17）`).
- Each new commit must have its own standalone work-summary file under `docs/` (do not keep appending to a single summary file).
- Recommended naming pattern for summaries: `docs/工作总结_YYYY-MM-DD_<topic>.md` (example: `docs/工作总结_2026-02-11_输入模块联调.md`).
- PRs should include: change summary, touched paths, test commands/results, risk notes, and rollback plan.

## Documentation Organization Principles
- 当任务存在明确“代码更改主题”时，必须先建立专题目录：`docs/{代码更改主题}/`。
- 该主题的主方案文档必须命名为：`docs/{代码更改主题}/{代码更改主题}.md`。
- 与该主题相关的所有文档（方案、实施记录、测试记录、阶段总结、专题工作总结等）必须统一放在 `docs/{代码更改主题}/` 下，不得分散到其他目录。
- `代码更改主题` 由当前任务目标总结得到，要求语义明确、可追溯，能够直接反映本次改造核心内容。
- `docs/archive/` 下的归档文档、历史阶段文档和非主线专题，默认不得继续出现在 `README.md`、`docs/README.md`、启动/测试指南、脚本提示语或新的专题方案文档的主索引中。
- 如确需引用归档文档，必须明确标注“历史参考”或“归档参考”，并说明该文档不能作为当前实现事实来源。

## Current Mainline And Evolution Constraints
- 当前默认交付目标仍是《歼灭追击战》固定路线 MVP。未获明确指示时，不得把主链路改写为通用 YOLO 主链路或 LLM 主链路。
- 已适配副本优先采用 `ROI + 固定流程`；未适配副本优先采用 `YOLO + 通用流程`。
- 静态 UI 元素优先采用固定 ROI / 规则法；动态空间目标优先采用 YOLO。
- 未来接入 LLM 时，LLM 只允许位于高层决策层，负责任务选择、链路切换、异常恢复和策略建议；不得直接输出底层键鼠动作，不得绕过 `GuardLayer`、熔断和本地控制层。
- 架构演进默认采用“外扩式重构”，优先新增抽象和适配层，不为跨游戏复用而推倒当前 DNF MVP 资产。
- `FixedRoutePipeline`、`MainViewReader`、`MinimapReader`、`StateReader`、ROI 资产、`room_scripts` 和实机分析文档默认视为可复用资产；除非有明确证据，不应整体废弃或重写。
- 后续若引入多副本支持，优先采用注册式入口，避免把副本特定逻辑继续散落到 `main.py`、UI 线程或全局分支判断中。
- 文档和注释必须明确区分“当前已实现事实”“中期规划”“长期预留”；未实现能力不得写成已落地事实。

## Security & Configuration Tips
- Do not commit runtime artifacts (`__pycache__/`, logs, temporary files) or private/local configs.
- Keep emergency stop behavior (`F12`) enabled in integration and real-run scenarios.
- This repository is for automation research in controlled environments; avoid unsafe production use.
