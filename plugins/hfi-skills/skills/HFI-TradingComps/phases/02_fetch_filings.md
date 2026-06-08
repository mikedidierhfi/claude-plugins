# Phase 02 — Fetch primary filings (SEC EDGAR)

For every confirmed ticker, pull the latest 10-Q and 10-K and all needed line items from EDGAR.

**Fast path:** `assets/build_comps.py` does this automatically (it calls `fetch_edgar` +
`company_facts`). You usually don't run this phase by hand.

**By hand / debugging:**
- `python assets/fetch_edgar.py <TICKERS>` → resolves CIK, finds latest 10-Q/10-K (accession, period,
  URL), caches the big JSON to `assets/_cache/`.
- `python assets/company_facts.py <TICKER>` → prints every EV line item (with citation) + the LTM
  bridge components. Use this to eyeball what was resolved.

**Watch for:**
- Ticker not found / no 10-Q-10-K → foreign filer (20-F/40-F) or wrong ticker → tell the user.
- `stale_only` / `missing` on a line item → the value was correctly dropped as too old; get it from
  the filing if needed. See [common_mistakes.md](../reference/common_mistakes.md) #1.
- `is_financial` signature → see [router.md](../router.md) financials branch.

Data source & etiquette: SEC EDGAR XBRL (`data.sec.gov`), descriptive User-Agent (set in
`fetch_edgar.py`, over/ridable via `SEC_UA`). See [edgar_api.md](../reference/edgar_api.md).
