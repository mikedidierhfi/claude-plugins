# Sanity checks — the QA gate (Phase 08)

Run these before delivering the workbook. They catch the errors that make an analyst look careless.
Most are encoded as `flags` by the engine; the rest are a human/agent read of the output.

## Per-company, mechanical
- [ ] **TEV > 0** and of sensible magnitude (TEV ≈ market cap for low-debt names; TEV > market cap
      when net debt is positive). A TEV far below market cap implies a large WC subtraction — verify.
- [ ] **Market cap ties to reality** — cross-check shares × price against a known market cap (e.g.,
      the figure on the exchange/quote page) within a few %. Big gaps ⇒ wrong share count (dual class?).
- [ ] **EBITDA ≥ EBIT** (D&A ≥ 0). If EBITDA < EBIT, D&A was resolved wrong.
- [ ] **Working capital sign** — fine if negative (subtracting a negative raises TEV); just confirm
      current assets/liabilities both came from the latest 10-Q (not stale).
- [ ] **No stale citations** — every EV line item's footnote date is within ~1 reporting period of the
      latest 10-Q. Any `stale_only` flag ⇒ the value was correctly dropped; supply it from the filing
      if it matters.
- [ ] **Every figure has a source** — filing accession/period for filing items; price source+timestamp;
      consensus provider+date for NTM. No un-sourced numbers.

## Multiples — plausibility
- [ ] TEV/EBITDA, TEV/EBIT, TEV/CFO, P/E land in believable ranges for the sector (single digits to
      ~40×; a 200× or negative-shown-as-number is a red flag). Denominator ≤ 0 should read `nm`.
- [ ] LTM vs NTM ordering is intuitive (NTM multiple usually < LTM if estimates grow). Big inversions
      warrant a glance.
- [ ] Cross-company consistency — all names on the same currency, units, and as-of date.

## Methodology fit
- [ ] **No financials forced in** — any `is_financial` name should be excluded or clearly caveated;
      TEV/EBITDA on a bank is meaningless.
- [ ] **Dual-class handled** — market equity sums all classes; footnote shows the split.
- [ ] **Leases** — finance leases only (unless operating-lease toggle was chosen and footnoted).

## Cross-check vs investor presentation (Phase 06)
- [ ] Compare computed clean EBITDA/EBIT/revenue to the company's most recent IR deck. Differences are
      expected (adjusted vs clean) — **document them**, don't hide them. A 2–3× gap usually means the
      deck shows "Adjusted EBITDA"; note it.

## Workbook integrity
- [ ] Open once in Excel: derived formulas compute (no `#REF!`/`#VALUE!`); CIQ cells populate or show
      `#NAME?` (add-in not loaded → expected, use fallback).
- [ ] Footnotes section lists every company's filings + price + consensus source; flags are visible.

If any check fails, fix the input or flag it explicitly in the workbook — never ship a silent error.
