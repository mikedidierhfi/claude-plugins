# LTM (Last-Twelve-Months) methodology

The denominators (EBIT, EBITDA, CFO, Net income) are flow figures. "Latest twelve months" is the
trailing-twelve-month figure as of the most recent 10-Q, built from filings — never a single
annual number unless that's all that's available.

## The bridge
```
LTM = latest fiscal year (10-K)  +  latest year-to-date (10-Q)  −  prior-year comparable YTD
```
Example (Apple, latest 10-Q ends 2026-03-28 = H1 FY26; 10-K ends 2025-09-27 = FY25):
```
LTM EBIT = FY25 ($133,050) + H1-FY26 ($86,737) − H1-FY25 ($72,421) = $147,366  ✓
```
The subtraction removes the part of the fiscal year that the current YTD already replaced.

## How the engine does it (`assets/company_facts.py: compute_ltm`)
For each flow concept it pulls every duration record from XBRL and selects:
- **FY**: a duration of ~350–380 days ending on the 10-K fiscal-year-end.
- **Current YTD**: the longest sub-annual duration ending on the 10-Q period-end (Q1 ≈ 90d,
  Q2 ≈ 180d, Q3 ≈ 270d).
- **Prior YTD**: a duration of the same length ending ~one year earlier.
Then `LTM = FY + YTD − priorYTD`. Each component is cited (start→end, value, accession).

## Edge cases (all handled, but review the `method`/`warn` fields)
- **Latest filing is a 10-K** (no newer 10-Q): `LTM = FY` (the fiscal-year value). `method="FY"`.
- **Can't cleanly match YTD/prior**: engine degrades to FY and sets `warn` — review it; the figure
  is the fiscal year, not a true trailing twelve months. Common for irregular filers / tag changes.
- **Recent acquisition or fiscal-year change**: the bridge still arithmetic-works but the LTM may
  mix pre/post-deal periods — note it if material (the analyst's judgment).
- **Banks/insurers**: often don't report `OperatingIncomeLoss` → EBIT/EBITDA LTM are blank by
  design (see [common_mistakes.md](../reference/common_mistakes.md) — financials don't fit).

## EBITDA
`LTM EBITDA = LTM EBIT + LTM D&A`, where EBIT = operating income and D&A is the depreciation &
amortization add-back (usually from the cash-flow statement, so it's an LTM flow built the same way).
This is a **clean / unadjusted** EBITDA. The company's own "Adjusted EBITDA" (stock-comp add-backs,
one-timers) will differ — that's what the investor-presentation cross-check ([phases/06](../phases/06_cross_check.md))
surfaces. Do not silently adopt the company's adjusted number; show both and footnote the difference.
