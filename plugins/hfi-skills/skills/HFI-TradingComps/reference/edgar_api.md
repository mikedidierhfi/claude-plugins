# SEC EDGAR API reference

The skill's filing backbone. Free, no login. Implemented in `assets/fetch_edgar.py`.

## Endpoints
| Purpose | URL |
|---|---|
| Ticker → CIK map | `https://www.sec.gov/files/company_tickers.json` |
| Filing index (submissions) | `https://data.sec.gov/submissions/CIK##########.json` (CIK zero-padded to 10) |
| XBRL company facts (all concepts) | `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json` |
| (single concept across filers) | `https://data.sec.gov/api/xbrl/frames/...` (not used) |

## Rules / etiquette
- **User-Agent is required** and must identify you (SEC blocks generic UAs). Set in `fetch_edgar.py`;
  override with env var `SEC_UA` (e.g., `"Hersh Family Investments research@…"`).
- Rate limit ~10 req/s. The skill makes a few requests per ticker and sleeps between tickers.
- Responses are cached to `assets/_cache/` (ticker map 7 days; submissions/companyfacts 1 day) so
  re-runs and tests are fast and polite.

## companyfacts structure (what the parser reads)
```
facts → {"us-gaap"|"dei" → {ConceptName → {"units" → {"USD"|"shares"|"USD/shares" → [records]}}}}
record = {start?, end, val, accn, fy, fp, form, filed, frame?}
```
- **Instant** concepts (balance sheet) have `end` only; **duration** concepts (income/cash-flow) have
  `start`+`end`. The parser uses this to match balance-sheet items to the 10-Q date and to build LTM.
- companyfacts contains only the **un-dimensioned default** series — dimensional breakdowns (by class,
  by segment) are NOT here. This is why multi-class share counts can be stale/ambiguous (see
  [common_mistakes.md](common_mistakes.md) #1, #3).

## Latest-filing detection
`latest_filings()` scans `filings.recent` for the most recent `10-Q` and `10-K`, returning accession,
filing date, report (period-end) date, primary document, and a built URL to the filing.
