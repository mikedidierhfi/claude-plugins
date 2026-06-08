# PLAN — architecture & data flow (for maintainers)

## What it does
Given a set of public-company tickers, build a footnoted Excel "Trading Statistics" workbook:
Total Enterprise Value (house definition) over LTM and NTM denominators, with valuation multiples —
from primary sources (SEC filings + live price + Capital IQ consensus).

## Data flow
```
tickers ─▶ fetch_edgar.py ──┐ (CIK, latest 10-Q/10-K, cached companyfacts)
                            ├─▶ company_facts.compute_line_items ──┐ (EV items + LTM, cited)
price  ─▶ market_price.py ──┘                                      │
consensus ─▶ consensus_input.py (CapIQ-formula / manual / skip) ───┤
                                                                   ▼
                                              build_comps.assemble  (TEV bridge + multiples + flags)
                                                                   ▼
                                              build_comps_xlsx.render (formula-driven workbook)
```
One command runs it all: `python assets/build_comps.py <TICKERS> --xlsx out.xlsx [--consensus-mode ...]`.

## Design principles
1. **Primary sources only**, every figure cited. No journalist/aggregator numbers.
2. **Never emit a confident-but-wrong number.** Staleness guard + missing-data flags; `nm` for
   non-positive denominators. Fail safe and loud, not silent.
3. **Implement the house EV definition exactly** (full-working-capital subtraction); flag deviations,
   don't auto-"correct" to textbook EV.
4. **Formula-driven output** so the analyst can audit and re-run every calc in Excel.
5. **Login-free where possible** (EDGAR, Yahoo); the only login (CapIQ consensus) is wired via the
   user's own Excel add-in, with manual/Chrome fallbacks. No credentials handled by the tool.
6. **Deterministic core, tested offline** (frozen fixtures + regression suite).

## File map
- `SKILL.md` entry · `router.md` decisions · `PLAN.md` this
- `phases/01..08` step guides · `core/*` methodology · `reference/*` tags/api/mistakes/QA/glossary
- `assets/fetch_edgar.py`, `company_facts.py`, `market_price.py`, `consensus_input.py`,
  `build_comps.py` (orchestrator), `build_comps_xlsx.py` (renderer), `xbrl_tags.json`
- `tests/` harness + frozen fixtures + `test_engine.py` (regression) + `test_render.py` (smoke)

## Known limitations (compile for the user)
- Wall Street **consensus needs the user's CapIQ** (no connector here) — via the Excel plug-in formulas.
- **Financials** (banks/insurers) don't fit the working-capital EV methodology — flagged, not forced.
- **Multi-class** share counts may need manual entry (companyfacts holds only the default series).
- Investor-deck cross-check is Chrome/analyst-driven (no single script).
