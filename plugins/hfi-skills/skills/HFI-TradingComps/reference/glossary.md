# Glossary

- **TEV (Total Enterprise Value)** — house numerator: market equity + long-term debt + finance leases
  + minority interest − working capital. See [core/ev_methodology.md](../core/ev_methodology.md).
- **Market equity value (market cap)** — shares outstanding × price.
- **Working capital** — total current assets − total current liabilities (a balance-sheet snapshot).
- **LTM (Last Twelve Months)** — trailing twelve months = FY (10-K) + YTD (10-Q) − prior-year YTD.
- **NTM (Next Twelve Months)** — forward twelve months, from Wall Street consensus (CapIQ).
- **EBIT** — earnings before interest & taxes = operating income (`us-gaap:OperatingIncomeLoss`).
- **EBITDA** — EBIT + depreciation & amortization. "Clean" = GAAP-derived (vs company "Adjusted EBITDA").
- **CFO** — cash flow from operations (`NetCashProvidedByUsedInOperatingActivities`).
- **NCI / minority interest** — noncontrolling interest; the equity in consolidated subs not owned by
  the parent (`us-gaap:MinorityInterest`). Added to EV.
- **Finance (capital) lease** — lease creating a debt-like obligation (ASC 842 finance lease /
  pre-842 capital lease). Added to EV (non-current portion). Operating leases excluded by default.
- **10-Q / 10-K** — quarterly / annual SEC filing for domestic issuers. (Foreign filers: 20-F/40-F.)
- **XBRL** — the tagged financial data in filings; the skill reads it via EDGAR companyfacts.
- **`nm`** — "not meaningful"; shown when a multiple's denominator is ≤ 0.
- **CIQ** — the Capital IQ Excel plug-in function, e.g. `=CIQ("AAPL","IQ_EBITDA_EST",IQ_NTM)`.
- **Dual-class** — multiple share classes (GOOG/GOOGL, BRK.A/BRK.B); market cap sums all classes.
- **Unclassified balance sheet** — no current/non-current split (banks, insurers) → no working capital.
