# Project Brief — battery-health-analytics

## TL;DR
Build a compact, testable analytics toolkit + web dashboard to **estimate/track battery State of Health (SoH)** and **evaluate how usage patterns impact degradation**. Start with Li‑ion datasets (MIT, HUST, TJU, XJTU), benchmark literature models, ensure no data leakage, and ship a runnable demo site + clean repo for hiring portfolio.

---

## Mission & Scope
- **Long‑term mission:** Improve visibility into battery health and lifetime; design **dispatch/charging strategies** that extend life while meeting grid/usage constraints.
- **Short‑term scope (current phase):**
  1) **Reproduce & benchmark** literature-style degradation models (power-law, exponential, calendar+cycle Arrhenius, simple RUL heuristics; optional PINN baseline).  
  2) **Estimate SoH online** from partial charge data (CC–CV slice features).  
  3) **Demonstrate impact of usage patterns** with counterfactual simulations; lay hooks for control/optimization later.

**Non-goals (current phase):** Full electrochemical P2D modeling, embedded BMS firmware, production-grade microservices, or exhaustive hyperparameter sweeps.

---

## Users & Outcomes
- **Target users:** Battery/analytics engineers, PMs, data scientists evaluating SoH pipelines, hiring teams (Voltaiq-like orgs).
- **Success criteria (MVP):**
  - Reproducible pipeline: ingest → feature extract → fit → validate → report.
  - Dashboard shows **SoH trajectory**, **uncertainty**, **residual diagnostics**, and **usage-pattern "what-ifs."**
  - **Leakage-safe** time splits; monotonic SoH constraints enforced (soft tolerance).
  - Tests covering features, leakage, synthetic recovery, residual whiteness, golden-dataset metrics.
  - Clean README, examples, and deployable demo (local or hosted).

---

## Datasets (initial)
- Public Li‑ion cycle datasets: **MIT** fast-charge, **HUST** LFP multi-stage discharge, **TJU** NCA/NCM, **XJTU** NCM.  
- Assumption: local copies or lightweight scripts to fetch small slices.  
- **Data policy:** Keep small "golden" slices in-repo; gate larger data with DVC or download script.

---

## Key Concepts & Constraints
- **Data leakage to avoid:** using future cycles or full-cycle aggregates when claiming "online" estimation; mixing test cycles/units into training; protocol info that won't be available online.
- **Physics priors:** SoH ∈ [0,1], **monotone non‑increasing** (allow tiny bounce ε), temperature/DoD accelerate aging (Arrhenius-like).
- **Evaluation:** time-based splits; metrics (MAE/MAPE/RMSE), **residual whiteness** (Ljung–Box), **input‑residual independence**, calibration if intervals used.
- **User preference:** minimal boilerplate; clear, small API; **grammar‑of‑graphics style viz** (e.g., Vega‑Lite), not Plotly‑style imperative charts.

---

## Tech Stack
- **Core analytics (Python):** `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn` (+ optional `jax`/`pytorch` later).  
- **Web app (JS):** **SvelteKit** (or Next.js) + **Vega‑Lite** or **Observable Plot**; minimal backend via **FastAPI** (only if needed).  
- **Testing:** `pytest`, `hypothesis` (property‑based), `statsmodels` diagnostics.  
- **Lint/format:** `ruff`, `black`, `pre-commit`.  
- **Data contracts:** `pydantic` models.  
- **CI:** GitHub Actions (unit + synthetic tests on push; slow/golden nightly).

---

## Repo Structure (lean)
```
battery-health-analytics/
  README.md
  LICENSE
  pyproject.toml
  src/bha/
    __init__.py
    features.py          # CC–CV slice features (mean/std/kurtosis/skew/time/charge/slope/entropy)
    models.py            # Power-law, exponential, Arrhenius calendar+cycle, simple PINN stub
    metrics.py           # MAE/MAPE/RMSE, residual tests (Ljung–Box), calibration helpers
    simulate.py          # Synthetic generators to test recovery
    pipeline.py          # Fit/eval entrypoints, time-split utilities, leakage guards
  tests/
    test_features.py
    test_leakage.py
    test_system_id.py
    test_monotonicity.py
    test_golden.py       # asserts metrics on tiny fixed slices
  data/
    golden/              # tiny fixed CSVs (few cycles, few cells)
  notebooks/
    01_benchmarks.ipynb  # reproducible figures for README
  dashboard/             # SvelteKit/Next app with Vega-Lite charts
    ...
```

---

## Initial Features & Models
- **Features (from CC–CV pre‑full‑charge slice):** voltage/current mean, std, kurtosis, skew, charging time, accumulated charge, slope, entropy.  
- **Baseline models:**  
  - **Power-law:** SoH(k) = 1 − a·√k − b·k  
  - **Exponential/linear** variants  
  - **Arrhenius calendar+cycle** (temp & DoD scalings)  
  - **Online SoH estimator** using features + monotone regressor (isotonic post‑processing).  
  - *(Optional)* PINN-style regularizer later.

---

## Dashboard Views (MVP)
1) **Unit detail:** SoH trajectory with confidence band; residual plots and whiteness p‑values.  
2) **Cohort compare:** multiple cells; overlay degradation; filter by protocol/temp.  
3) **What‑if panel:** change usage parameters (temp, DoD, C‑rate) → counterfactual trajectory using chosen model.  
4) **Data quality:** missing data, outliers, time gaps.

---

## Testing Strategy (contracts & stats)
- **Pure unit:** shapes/ranges, no NaNs, correct CC–CV windowing, idempotence.
- **Property‑based:** resampling invariance; unit conversions.
- **System‑ID (synthetic):** recover known parameters within tolerance; RMSE cap; **Ljung–Box** p>0.05; residual–input cross‑corr ~0.
- **Monotonicity/bounds:** SoH in [0,1], non‑increasing within ε.
- **Golden regression:** fixed slice passes MAPE ≤ 2% and runtime < cap.
- **Leakage guards:** strict time splits; online mode bans future info.

---

## Milestones
**Day 1 (now):**
- `features.py`, `simulate.py`, `models.py` (power‑law & exponential), `pipeline.py` (time split), tests: features/monotonicity/system‑ID/leakage.  
- `01_benchmarks.ipynb` to generate README plots.  
- Minimal SvelteKit page rendering a Vega‑Lite SoH chart.

**Day 2–3:**
- Arrhenius calendar+cycle model; cohort compare view; golden-dataset tests; README polish with results.  
- Optional small FastAPI for serving predictions.

**Stretch:**
- Uncertainty (bootstrap), calibration test.  
- Counterfactual what‑if sliders.  
- PINN regularizer stub.

---

## Style & Principles
- Prefer **small, pure, composable** functions; functional core, imperative shell.  
- Short modules; explicit IO types; type hints.  
- Clear docstrings with equations and units.  
- Guardrails against leakage are **first-class**.  
- Minimal dependencies; no heavy ML unless justified.

---

## Risks & Mitigations
- **Data inconsistency** → pydantic schemas + data validation step.  
- **Overfitting/optimism** → strict time-based CV + golden tests.  
- **Viz complexity** → use Vega‑Lite grammar; keep views focused.  
- **Scope creep** → stick to the three short‑term objectives.

---

## "What good looks like" (acceptance)
- `pytest -q` passes locally & in CI; coverage on core ~80%+.  
- README shows benchmark plots and links to dashboard.  
- Dashboard loads sample data and supports one what‑if scenario.  
- Repro commands: `make setup`, `make test`, `make demo`.

---

## Glossary
- **SoH:** Ratio current capacity / nominal capacity (∈ [0,1]).  
- **Leakage:** Training/test contamination via time, protocol, or features derived from future data.  
- **Residual whiteness:** Residuals behave like white noise (no autocorr).

---

## Contact / Persona Notes (for memory)
- Developer prefers **clarity over boilerplate**, concise APIs, typed Python, and **grammar-of-graphics** viz (Vega‑Lite/Observable Plot).  
- Background: MS focus in control & power systems; self-taught batteries; aiming for roles like Voltaiq.  
- Tone: practical, shipping‑oriented; keep explanations brief and actionable.
