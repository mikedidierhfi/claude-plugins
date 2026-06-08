# Tests & self-check — the "same results every time" guarantee

Run the whole thing before relying on a comp:
```
python assets/selfcheck.py
```
It checks the environment (Python, openpyxl), SEC EDGAR reachability (soft, cache-aware), and runs
the full offline regression suite. Exit 0 = healthy / reproducible.

## Suite (all deterministic, offline — frozen fixtures, no network)
| File | Locks | Count |
|------|-------|------:|
| `test_engine.py` | XBRL line-item extraction + the LTM bridge, the **staleness guard**, and the financial/multi-class signatures — against frozen fixtures (AAPL, MSFT, JPM, BRK-B) | 33 |
| `test_valuation.py` | The **orchestrator valuation math** (`build_comps.assemble`): TEV bridge, every multiple, `nm`/blank handling, `$mm` scaling, `--shares` override, `is_financial` — on synthetic inputs (network monkeypatched) | 20 |
| `test_render.py` | The Excel renderer shape: live derived formulas, `=CIQ()` NTM formulas, manual-consensus statics, inputs carried, flags shown | 11 |

Fixtures are built by `_framework/make_fixture.py` (trims a full SEC companyfacts JSON to just the
concepts the skill uses, so they're small and frozen).

## What "same results" means here
- **Deterministic given the same inputs.** The 64 assertions prove that identical filings + price
  produce identical EV, denominators, and multiples — forever. The Excel workbook re-expresses this
  exact math as live formulas (verified in `test_render` to reference the right cells), so the
  spreadsheet and the engine agree by construction.
- **Live data changes by design.** "Latest 10-Q/10-K" and "today's price" move over time — that's
  correct. To reproduce a *past* run, pin it via the footnoted accession numbers + price date (the
  `_cache/` JSON and the workbook footnotes capture exactly what was used).
- **Fails safe, never silently wrong.** Stale/missing/odd data is flagged, not guessed (staleness
  guard on instants and flows; `nm` for non-positive denominators; `is_financial` off-ramp).
