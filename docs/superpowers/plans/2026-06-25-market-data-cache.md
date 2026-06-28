# Market Data Cache Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add resilient local CSV caching for network market data and expose cache controls in the existing Streamlit application.

**Architecture:** Keep existing network loaders intact and wrap them with cache orchestration in `load_price_data`. Keep local CSV loading separate, and make Streamlit initialize all branch-dependent parameters before loading data.

**Tech Stack:** Python, pandas, Streamlit, pytest, AkShare, yfinance

---

### Task 1: Cache behavior tests

**Files:**
- Create: `tests/test_data_loader_cache.py`
- Modify: `core/data_loader.py`

- [x] Write failing tests for cache hit, disabled cache, corrupt cache fallback, cache clearing, normalized OHLCV, and local CSV loading.
- [x] Run `python -m pytest tests/test_data_loader_cache.py -v` and confirm failures are caused by missing cache APIs.
- [x] Implement the minimal cache helpers and orchestration.
- [x] Re-run the focused tests and confirm they pass.

### Task 2: Streamlit integration

**Files:**
- Modify: `app.py`

- [x] Add proxy environment cleanup before network-related imports.
- [x] Add cache checkbox and clear button.
- [x] Restore data source selection and local CSV upload while preserving both market branches.
- [x] Pass `source`, `disable_proxy`, and `use_cache` to `load_price_data`.
- [x] Run `python -m py_compile app.py core/data_loader.py`.

### Task 3: End-to-end verification

**Files:**
- Verify: `app.py`
- Verify: `core/data_loader.py`
- Verify: `tests/test_data_loader_cache.py`

- [x] Run the complete test suite.
- [x] Import the application dependencies and loader APIs.
- [x] Start Streamlit headlessly with a short timeout and confirm the server reaches its ready state.
- [x] Review the final diff against every user requirement.
