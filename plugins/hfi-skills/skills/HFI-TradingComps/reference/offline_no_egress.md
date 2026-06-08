# No-egress fallback — running the skill when the sandbox can't reach the internet

Some chat / code-execution sandboxes block outbound network. Run `python3 assets/selfcheck.py`: if
**"SEC EDGAR reachable"** is PASS, ignore this file — everything runs directly. If it's WARN/FAIL,
use this fallback. It avoids the multi-MB `companyfacts`/`submissions` files by fetching EDGAR's small
**per-concept** endpoints with the agent's web/browser tool, then assembling them into the exact
`_cache/` files the normal pipeline reads. Filing dates are derived from the concept data — no
`submissions` download needed. Results are identical to the direct path (locked by `tests/test_offline.py`).

## Steps (per ticker)
1. **Get the CIK.** web_fetch the tiny atom feed and read `<cik>`:
   `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker=AAPL&type=10-K&count=1&output=atom`
2. **List the small files to fetch:**
   `python3 assets/offline_fetch.py plan AAPL 320193`
   → prints ~30 `companyconcept` URLs (each a few KB–~100KB) + the filename to save each as.
3. **Fetch each URL** with the web/browser tool; save the JSON into `_cache/concepts_AAPL/<save_as>`.
   (A 404 just means the issuer doesn't report that concept — skip it.)
4. **Assemble the cache:**
   `python3 assets/offline_fetch.py assemble AAPL 320193`
   → writes `_cache/companyfacts_CIK0000320193.json` + `_cache/submissions_CIK0000320193.json`
     + the ticker→CIK map entry.
5. **Get the price** with the web tool (e.g., Yahoo quote), then run the normal pipeline offline,
   injecting the price (and Class-A shares for Up-C names):
   `python3 assets/build_comps.py AAPL --prices "AAPL=307.34" --xlsx out.xlsx`
   (`build_comps` reads the pre-populated `_cache/`, so no network is needed.)

## Notes
- The offline assembly + the normal pipeline produce the **same numbers** — only the fetch mechanism
  differs. The workbook footnotes a filing-folder URL (the exact primary-doc filename isn't available
  offline) — still a valid, citeable EDGAR link.
- For several tickers, repeat steps 1–4 per ticker, then a single `build_comps.py A B C --prices "A=..,B=..,C=.."`.
- This is the same `--prices` override you'd use to pin a price for a reproducible/as-of run.
