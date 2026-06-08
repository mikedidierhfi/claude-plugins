# Common mistakes (and how this skill avoids them)

Hard-won from real edge-testing (JPM, Berkshire, Apple, Microsoft). Read before trusting output.

## 1. Stale XBRL "default" values — the silent killer
Some issuers leave an old value in the un-dimensioned XBRL series (e.g., JPM's `LongTermDebt` last
appears in **2014**; Berkshire's plain `EntityCommonStockSharesOutstanding` is from **2011**).
Naively taking "the latest record for the tag" yields a number years out of date.
→ **Fix in place:** `resolve_instant` only accepts a value whose period-end is within ±~400 days of
the target; otherwise it skips the tag and, if nothing fresh exists, returns *missing* with a
`stale_only` diagnostic. **Never** report a multi-year-old figure. If a needed item comes back
missing, get it from the actual filing/cover page — don't reach for the stale series.

## 2. Financials & alternative asset managers don't fit this methodology
Banks, insurers, and **alternative asset managers** (BX, KKR, ARES, OWL, APO, CG, TPG, …) use an
**unclassified balance sheet** (no current assets/liabilities → no working capital) and don't report
`OperatingIncomeLoss` (no EBIT/EBITDA). CFO is volatile/negative; alt managers also carry large
consolidated-fund/insurance **NCI** that inflates any TEV (e.g., KKR ~$47.5B).
→ The engine sets `is_financial` and flags loudly. **Switch frameworks**: banks/insurers → P/E, P/TBV,
P/B; **alt managers → AUM, FRE, Distributable Earnings** (P/E, P/FRE, P/Distributable, mkt cap/AUM).
Don't force TEV/EBITDA. Full playbook + tools: **[`financials_and_alts.md`](financials_and_alts.md)**.

## 3. Dual-class / Up-C share counts
For GOOG/GOOGL, BRK.A/BRK.B, FOX/FOXA, and Up-C alt managers, market equity = **Σ(class shares ×
class price)** and the single-ticker `EntityCommonStockSharesOutstanding` is often class-specific or
stale → engine returns shares `None` (flagged).
→ Get the **Class A** count from the 10-Q cover and pass `build_comps.py --shares "TKR=<count>"`; for
Up-C names also report an **economic** market cap (Class A + operating-group units). Footnote the split.

## 4. Double-counting debt
Adding *total* debt **and** subtracting working capital double-counts the current portion of debt
(it lives in current liabilities). → House definition uses **long-term debt only** and **non-current
finance leases only**; current portions are netted via working capital. Keep it that way.

## 5. Finance vs operating leases
Post-ASC 842, "capital lease obligations" = **finance** lease liabilities. Operating leases are a
separate line and are **excluded by default** (per house spec; optional toggle). Don't add both.

## 6. Adjusted vs clean EBITDA
The company's "Adjusted EBITDA" (add-backs for SBC, restructuring, etc.) ≠ clean EBITDA = EBIT + D&A.
→ Compute the clean GAAP figure; show the company's adjusted number only in the cross-check row,
labeled, with the deck cited. Mixing them silently overstates EBITDA and understates multiples.

## 7. Shares: cover page vs balance sheet
Use the **cover-page** `dei:EntityCommonStockSharesOutstanding` (most recent, dated near filing) for
market cap — not the weighted-average diluted share count (that's for EPS) and not an old
balance-sheet count. The engine prefers the cover-page tag (freshest, within the staleness window).

## 8. Foreign private issuers
20-F / 40-F filers (no 10-Q/10-K) are out of scope — surface to the user rather than guessing.

## 9. Negative / zero denominators
Never print a negative or wild multiple. Denominator ≤ 0 → **`nm`**. Negative LTM EBIT/NI happens
(losses) and is real — show `nm`, not a misleading positive.

## 10. Price timing & weekends
"Today's price" = most recent close if markets are shut (the run date here, 2026-06-07, is a Sunday →
Friday's close). Footnote the price's as-of timestamp. Never use a recalled/round-number price.

## 11. Units
Default `$ in millions`, shares in millions, multiples in `x`. Market cap of a mega-cap is millions
(e.g., $4,514,012mm = $4.5T). Don't mix $ and $mm in the same column.
