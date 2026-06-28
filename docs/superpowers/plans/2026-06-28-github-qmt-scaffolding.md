# GitHub and QMT Scaffolding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the existing quant platform for GitHub and future paper/QMT execution without changing current Streamlit behavior.

**Architecture:** Add isolated broker, data-quality, and metric modules with no application wiring. Add repository metadata, configuration, placeholder directories, and documentation around the existing runtime.

**Tech Stack:** Python, pandas, NumPy, PyYAML, pytest, Streamlit

---

### Task 1: Test the new Python APIs

**Files:**
- Create: `tests/test_brokers.py`
- Create: `tests/test_data_quality.py`
- Create: `tests/test_metrics.py`

- [x] Write tests describing BaseBroker, PaperBroker, QMT stub, OHLCV checks, and metrics.
- [x] Run the focused tests and confirm they fail because modules are missing.

### Task 2: Implement isolated modules

**Files:**
- Create: `brokers/__init__.py`
- Create: `brokers/base_broker.py`
- Create: `brokers/paper_broker.py`
- Create: `brokers/qmt_broker_stub.py`
- Create: `core/data_quality.py`
- Create: `core/metrics.py`

- [x] Implement the smallest APIs needed by the tests.
- [x] Run focused tests until green.

### Task 3: Add repository scaffolding and docs

**Files:**
- Create: `.gitignore`, `LICENSE`, `configs/default.yaml`
- Create: `docs/roadmap.md`, `docs/qmt_integration_plan.md`
- Create: `data_cache/.gitkeep`, `outputs/.gitkeep`
- Modify: `README.md`, `requirements.txt`

- [x] Add the requested repository files without modifying `app.py`.
- [x] Validate ignore rules and YAML syntax.

### Task 4: Verify the repository

- [x] Run the complete pytest suite.
- [x] Compile all Python source files.
- [x] Import all new modules.
- [x] Start Streamlit headlessly and confirm readiness.
