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
        + Minority / noncontrolling interest      (latest 10-Q, equity + redeemable/mezzanine)
        + Preferred equity                        (latest 10-Q, carrying value)
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
  `shares_class_i x price_class_i` across classes. The engine auto-detects when the cover lists
  multiple distinct share counts and **flags** it so you supply the total via `--shares`. (When a
  filer instead reports one *combined* `CommonStockSharesOutstanding` — as Alphabet does — that total
  is already correct and no flag fires.) Footnote the split when you override.

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

**Minority / noncontrolling interest** — `us-gaap:MinorityInterest` (equity-section NCI) **summed
with** `us-gaap:RedeemableNoncontrollingInterestEquityCarryingAmount` (mezzanine NCI), since a name
can carry both in different balance-sheet sections. Add the full carrying amount of each. The engine
sums them automatically and footnotes the split when redeemable NCI is present.

**Preferred equity** — a claim senior to common, added to EV like minority interest. The engine
captures redeemable/mezzanine preferred (`TemporaryEquityCarryingAmountAttributableToParent`,
`RedeemablePreferredStockCarryingAmount`) at carrying value, falling back to permanent
`PreferredStockValue`. **Caveat:** `PreferredStockValue` is *par*, which usually understates the
liquidation/redemption preference — when preferred is captured at par, the engine flags it so the
analyst can verify the liquidation value in the filing and override if material. $0 for the vast
majority of issuers (no preferred outstanding).

**Working Capital** — `Total Current Assets (us-gaap:AssetsCurrent)` minus
`Total Current Liabilities (us-gaap:LiabilitiesCurrent)`, both from the latest 10-Q balance sheet.
Subtract the result. (If WC is negative, subtracting it *increases* TEV — that is correct and
expected for many retailers/operators.)

### Analyst note — how this differs from textbook EV
Textbook EV = Market Cap + Total Debt + Preferred + Minority Interest − **Cash & equivalents**.
Like textbook EV, the house definition adds debt, preferred, and minority interest; **the sole
difference is the deduction** — the house definition subtracts **all net working capital**, not just
cash. Effect: it also nets out non-cash current assets (receivables, inventory, prepaids) against
non-debt current liabilities (payables, accruals). For a working-capital-light business the two are
close; for a working-capital-heavy business they diverge materially. Two related house choices that
the engine **flags rather than auto-adjusts** (your call): (a) long-term marketable-securities /
investment portfolios are *not* netted (only current working capital is); (b) preferred captured at
par may understate liquidation value. Always present the house number as the headline; a textbook-EV
reconciliation row can be added as an optional line.

## Show the bridge in Excel
Render every term as its own row so the user can audit the build-up:
```
Shares outstanding (mm)              [from 10-Q cover]
x Price ($)                          [latest close, dated]
= Market equity value ($mm)
+ Long-term debt                     [10-Q]
+ Finance lease obligations (LT)     [10-Q]
+ Minority interest                  [10-Q]   (equity + redeemable NCI, summed)
+ Preferred equity                   [10-Q]   ($0 for most issuers)
- Working capital                    [= Curr. assets - Curr. liabilities]
    Total current assets             [10-Q]   (sub-row)
    Total current liabilities        [10-Q]   (sub-row)
= Total Enterprise Value ($mm)
```
Each sourced line carries a footnote marker tying it to the filing (type, period end, accession #).
