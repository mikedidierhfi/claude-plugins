# Denominator definitions

All denominators are computed on an **LTM** basis from filings (see [ltm_methodology.md](ltm_methodology.md))
and, separately, on an **NTM** basis from Wall Street consensus (see [consensus_sourcing.md](consensus_sourcing.md)).
Figures are "clean" (as-reported per GAAP), not company-adjusted, unless explicitly noted.

| Denominator | Definition | Primary XBRL tag(s) | Notes |
|---|---|---|---|
| **EBIT** | Operating income | `us-gaap:OperatingIncomeLoss` | The GAAP operating income line. Excludes non-operating items, interest, taxes. |
| **EBITDA** | EBIT + D&A | EBIT (above) + `DepreciationDepletionAndAmortization` / `DepreciationAmortizationAndAccretionNet` / `DepreciationAndAmortization` | D&A taken from the cash-flow statement (most complete). Clean, unadjusted. |
| **CFO** | Net cash from operating activities | `us-gaap:NetCashProvidedByUsedInOperatingActivities` | As-reported operating cash flow. For some financials this is volatile/negative → multiple shows `nm`. |
| **Net income** | Net income attributable to the company | `us-gaap:NetIncomeLoss` (fallback `ProfitLoss`) | Attributable to parent (after NCI). Used for TEV/NI per house spec and for the P/E memo. |
| Revenue (context) | Total revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` / `Revenues` | Shown for context/scale; not a multiple denominator by default. |

## Multiples built from these (numerator = TEV; see [ev_methodology.md](ev_methodology.md))
- **TEV / EBITDA** — the workhorse; capital-structure-neutral, pre-D&A.
- **TEV / EBIT** — capital-structure-neutral, post-D&A (capital-intensity aware).
- **TEV / CFO** — cash-based; useful where accruals distort EBITDA.
- **TEV / Net income** — per the house spec. *Note:* this is non-standard (an equity metric under an
  enterprise numerator); a **P/E (market equity ÷ NI)** memo row is included for the conventional read.
- Each is shown **LTM** and **NTM**.

## Guardrails
- **Negative or zero denominator → `nm`** (not meaningful). Never print a negative or absurd multiple.
- **EBITDA must be ≥ EBIT** (D&A ≥ 0). If not, D&A resolved wrong — investigate (see sanity_checks).
- **Adjusted vs reported:** the company's "Adjusted EBITDA"/"non-GAAP EPS" will usually exceed the
  clean figure. Keep the clean GAAP figure as the computed default; report the company's adjusted
  number only in the cross-check row, clearly labeled, with the source deck cited.
