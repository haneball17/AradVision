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
- PRs should include: change summary, touched paths, test commands/results, risk notes, and rollback plan.

## Security & Configuration Tips
- Do not commit runtime artifacts (`__pycache__/`, logs, temporary files) or private/local configs.
- Keep emergency stop behavior (`F12`) enabled in integration and real-run scenarios.
- This repository is for automation research in controlled environments; avoid unsafe production use.
