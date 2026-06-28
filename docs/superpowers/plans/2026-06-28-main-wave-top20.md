# Main Wave Top20 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rule-based main-wave A-share candidate ranking page without changing the existing single-stock backtest flow.

**Architecture:** Keep factor calculations in focused modules and orchestrate downloads/scoring in `selection/main_wave_selector.py`. Add one early page route to `app.py`, rendering the new page independently and leaving the existing code path intact.

**Tech Stack:** Python, pandas, NumPy, Streamlit, pytest

---

### Task 1: Factor and filter APIs

**Files:**
- Create: `tests/test_main_wave_factors.py`
- Create: `stock_pools/sector_map.py`
- Create: `factors/momentum_factors.py`
- Create: `factors/volume_price_factors.py`
- Create: `factors/sector_factors.py`
- Create: `factors/risk_filters.py`

- [x] Write tests for sector normalization, momentum, volume-price, sector strength and filters.
- [x] Run tests and confirm missing-module failures.
- [x] Implement minimal factor/filter functions.
- [x] Run focused tests until green.

### Task 2: Candidate selection orchestration

**Files:**
- Create: `tests/test_main_wave_selector.py`
- Create: `selection/main_wave_selector.py`

- [x] Write network-free tests for scoring, Top N, date selection and failed-symbol skipping.
- [x] Confirm tests fail before implementation.
- [x] Implement loader orchestration and ranking.
- [x] Run focused tests until green.

### Task 3: Streamlit route and documentation

**Files:**
- Modify: `app.py`
- Create: `docs/main_wave_strategy.md`
- Modify: `docs/roadmap.md`

- [x] Add the early two-page route and independent render function.
- [x] Add inputs, result table, errors, empty state and CSV download.
- [x] Document factors, score, filters, future labels/news and risk warning.

### Task 4: Verification and feature commit

- [ ] Run all tests and Python compilation.
- [ ] Verify the selector with deterministic sample data.
- [ ] Start Streamlit headlessly and verify both page labels are present.
- [ ] Commit all changes on `feature/main-wave-top20` without merging into `main`.
