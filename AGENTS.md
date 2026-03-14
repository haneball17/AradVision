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

## Security & Configuration Tips
- Do not commit runtime artifacts (`__pycache__/`, logs, temporary files) or private/local configs.
- Keep emergency stop behavior (`F12`) enabled in integration and real-run scenarios.
- This repository is for automation research in controlled environments; avoid unsafe production use.
