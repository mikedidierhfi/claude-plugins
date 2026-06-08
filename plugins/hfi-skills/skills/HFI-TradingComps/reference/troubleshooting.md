# Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Ticker not found in SEC map` | Wrong ticker, or foreign filer (20-F/40-F), or newly listed | Confirm ticker; tell the user if it's a foreign filer (out of scope). |
| Line item `missing` with a `stale_only` note | Issuer leaves an old value in the default XBRL series; staleness guard dropped it | Correct behavior. If the item matters, read it from the latest 10-Q and supply manually. |
| Shares = None, market cap blank | Multi-class issuer or unusual tagging (e.g., BRK) | Get share counts per class from the 10-Q cover; market equity = Σ(class shares × class price). |
| Whole name flagged `FINANCIAL ISSUER` | Bank/insurer: unclassified balance sheet, no operating income | Exclude from the comp set or use a financials framework (P/E, P/TBV, P/B). |
| EBITDA < EBIT in output | Wrong D&A tag resolved (or negative D&A) | Check `depreciation_amortization` citation; verify against the cash-flow statement. |
| Price `fallback_needed: true` | Yahoo + stooq both failed/blocked | Read last close via Chrome (`finance.yahoo.com/quote/<TKR>`) or have the user paste it. |
| NTM cells show `#NAME?` in Excel | Capital IQ add-in not loaded/enabled | Enable the add-in, or use manual paste (`--consensus`), or CapIQ web via Chrome. |
| NTM CFO blank but others fill | `IQ_CFO_EST` consensus coverage is thin | Expected; leave blank or source manually. EBITDA/EBIT/NI are reliable. |
| LTM figure `warn`: "degraded to FY" | YTD/prior-YTD periods couldn't be matched (tag change, odd fiscal calendar) | Figure is the fiscal year, not true TTM; verify and note, or compute by hand. |
| Network error fetching EDGAR | Transient / UA blocked | `fetch_edgar.py` retries; set a descriptive `SEC_UA` env var; re-run (cache makes it cheap). |
| `#REF!`/`#VALUE!` in workbook | A referenced input cell was unexpectedly text | Check the input row; re-run; report if reproducible. |
| Multiple shows `nm` | Denominator ≤ 0 (losses, negative bank CFO) | Correct — not an error. |

Run `python tests/test_engine.py` (33 offline assertions) to confirm the engine itself is healthy
before chasing a data issue.
