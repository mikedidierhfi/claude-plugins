# Phase 04 — Build the Enterprise Value bridge

Assemble TEV per the house definition (see [core/ev_methodology.md](../core/ev_methodology.md)).
**Fast path:** `build_comps.py: assemble()` computes it.

```
Market equity value = shares (10-Q) × price
TEV = market equity + long-term debt + finance leases + minority interest + preferred − working capital
working capital = total current assets − total current liabilities
```
- Minority interest sums equity-section NCI + redeemable (mezzanine) NCI. Preferred equity is added
  at carrying value ($0 for most issuers; par-value capture is flagged to verify liquidation value).
- Missing add-backs (lease/minority/preferred) are treated as $0 **and flagged** — confirm that's
  right (most issuers genuinely have none).
- Other auto-flags to act on: multiple share classes detected (supply total via `--shares`), non-USD/
  ADR financials (currency mismatch vs price), material long-term investments not netted (your call),
  and EBITDA period-basis mismatch (D&A not on an LTM basis).
- Missing working capital (financials) → omitted **and flagged** → reconsider including the name.
- **Debt completeness (any filer):** the XBRL pull can miss debt under custom/related-party tags. The
  engine reconciles total liabilities vs what it captured and, if a material gap remains, **reads the
  actual 10-Q balance sheet** (`assets/verify_filing.py`) and lists the debt-like lines + a suggested
  figure in the flag. Verify it (exclude equity-linked warrants per the house def) and re-run with
  `--debt "<TKR>=<$mm>"`. See [common_mistakes.md](../reference/common_mistakes.md) #1a.
- In the workbook these are **live Excel formulas**, so the user can audit/trace each term.

Verify against [sanity_checks.md](../reference/sanity_checks.md): TEV > 0, ties to market cap ± net debt.
