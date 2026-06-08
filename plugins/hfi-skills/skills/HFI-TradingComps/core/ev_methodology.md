# Enterprise Value — House Methodology (authoritative spec)

This is the **exact** definition the skill must implement. It is a deliberate house convention.
Do **not** silently replace it with textbook EV. Where it differs from the textbook, an analyst
note is provided so the result can be explained — but the default calculation is this one.

## Numerator: Total Enterprise Value (TEV)

```
(1) Market Equity Value = Shares Outstanding (latest 10-Q) x Latest stock price
(2) TEV = Market Equity Value
        + Long-term debt                         (latest 10-Q)
        + Capital / finance lease obligations     (latest 10-Q, non-current)
        + Minority / noncontrolling interest      (latest 10-Q)
        - Working Capital
                where Working Capital = Total Current Assets - Total Current Liabilities (latest 10-Q)
```

### Line-by-line

**Shares Outstanding** — Use the most recent actual shares outstanding from the latest 10-Q.
Preference order:
1. `dei:EntityCommonStockSharesOutstanding` — the cover-page count, dated *as of the filing date*
   (the freshest available, the count an analyst uses for market cap).
2. `us-gaap:CommonStockSharesOutstanding` — balance-sheet date count (fallback).
- **Dual-class:** if the issuer has multiple share classes (e.g., GOOGL/GOOG, BRK.A/B), sum
  `shares_class_i x price_class_i` across classes. Default config handles the common single-class
  case; flag dual-class issuers in `phases/01_intake.md` and confirm handling. Footnote the split.

**Latest stock price** — Most recent trade/close as of the run date. If markets are closed
(weekend/holiday/after-hours), use the most recent close and footnote the date/time. Source:
stooq.com (no login) → Chrome (Yahoo/Google Finance) fallback. Never a hard-coded or remembered price.

**Long-term debt** — `us-gaap:LongTermDebtNoncurrent` preferred (non-current portion only).
- Do **not** add the current portion of long-term debt or short-term borrowings separately:
  those sit in **current liabilities** and are therefore already netted out by the
  `- Working Capital` term. Adding them again would double-count. This is why the house
  definition says "long-term debt."
- If a filer only reports a combined `LongTermDebt` (incl. current), prefer the explicit
  `...Noncurrent` tag; if unavailable, use combined and *do not* also rely on WC to net current
  debt — instead footnote the treatment. (See `reference/common_mistakes.md`.)

**Capital / finance lease obligations** — `us-gaap:FinanceLeaseLiabilityNoncurrent` (post-ASC 842)
or `us-gaap:CapitalLeaseObligationsNoncurrent` (pre-842). Non-current only (current portion is in
current liabilities → already in WC). **Operating lease liabilities are excluded by default**
(the user said "capital lease obligations"). Provide an optional toggle to include operating
leases; if toggled on, footnote it.

**Minority / noncontrolling interest** — `us-gaap:MinorityInterest` (equity-section NCI). Also add
`us-gaap:RedeemableNoncontrollingInterestEquityCarryingAmount` if present (mezzanine NCI). These are
non-current; add the full carrying amount.

**Working Capital** — `Total Current Assets (us-gaap:AssetsCurrent)` minus
`Total Current Liabilities (us-gaap:LiabilitiesCurrent)`, both from the latest 10-Q balance sheet.
Subtract the result. (If WC is negative, subtracting it *increases* TEV — that is correct and
expected for many retailers/operators.)

### Analyst note — how this differs from textbook EV
Textbook EV = Market Cap + Total Debt + Preferred + Minority Interest − **Cash & equivalents**.
The house definition subtracts **all net working capital**, not just cash. Effect: it also nets
out non-cash current assets (receivables, inventory, prepaids) against non-debt current
liabilities (payables, accruals). For a working-capital-light business the two are close; for a
working-capital-heavy business they diverge materially. Always present the house number as the
headline and, if useful, a textbook-EV reconciliation row can be added as an optional line.

## Show the bridge in Excel
Render every term as its own row so the user can audit the build-up:
```
Shares outstanding (mm)              [from 10-Q cover]
x Price ($)                          [latest close, dated]
= Market equity value ($mm)
+ Long-term debt                     [10-Q]
+ Finance lease obligations (LT)     [10-Q]
+ Minority interest                  [10-Q]
- Working capital                    [= Curr. assets - Curr. liabilities]
    Total current assets             [10-Q]   (sub-row)
    Total current liabilities        [10-Q]   (sub-row)
= Total Enterprise Value ($mm)
```
Each sourced line carries a footnote marker tying it to the filing (type, period end, accession #).
