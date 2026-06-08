# Phase 04 — Build the Enterprise Value bridge

Assemble TEV per the house definition (see [core/ev_methodology.md](../core/ev_methodology.md)).
**Fast path:** `build_comps.py: assemble()` computes it.

```
Market equity value = shares (10-Q) × price
TEV = market equity + long-term debt + finance leases + minority interest − working capital
working capital = total current assets − total current liabilities
```
- Missing add-backs (lease/minority) are treated as $0 **and flagged** — confirm that's right (most
  issuers genuinely have none).
- Missing working capital (financials) → omitted **and flagged** → reconsider including the name.
- In the workbook these are **live Excel formulas**, so the user can audit/trace each term.

Verify against [sanity_checks.md](../reference/sanity_checks.md): TEV > 0, ties to market cap ± net debt.
