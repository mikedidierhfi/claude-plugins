# Router — decision tree

Use this to choose the right data path at each step. The happy path is fully automated; the
branches handle the real-world messiness an All-America analyst expects.

## Top-level flow
```
01 intake (prompt for tickers + options)
  -> 02 fetch filings (EDGAR)        [assets/fetch_edgar.py]
  -> 03 market data (price)          [assets/market_price.py]
  -> 04 build EV bridge              [assets/build_comps.py assemble()]
  -> 05 denominators (LTM + NTM)     [assets/company_facts.py + consensus_input.py]
  -> 06 cross-check vs investor deck [Chrome / WebFetch]      (optional but recommended)
  -> 07 build Excel                  [assets/build_comps_xlsx.py]
  -> 08 QA                           [reference/sanity_checks.md]
```
The simplest invocation is just: `python assets/build_comps.py <TICKERS> --xlsx <out> [--consensus <json>]`
which runs 02→05 and 07 in one shot. Use the step files when something needs hand-holding.

## Branch: stock price
- Try `market_price.py` (Yahoo chart API, keyless). If it returns a price → use it.
- If it returns `fallback_needed` (Yahoo + stooq both failed) → open the quote in **Chrome**
  (`finance.yahoo.com/quote/<TICKER>` or `google.com/finance`) and read the last price, OR ask the
  user to paste it. Never recall a price from memory. Footnote the source + timestamp either way.

## Branch: consensus / NTM (the login gap)
```
consensus connector wired in? (ToolSearch: capiq / factset / bloomberg / estimates)
  YES -> implement fetch_consensus_via_connector() in consensus_input.py and use it
  NO  -> user chose "chrome"? -> drive Chrome on their logged-in provider (Koyfin/TIKR/CapIQ/etc.),
                                  read NTM mean EBITDA/EBIT/CFO/NI, write into consensus.json
         user chose "paste"?  -> `python consensus_input.py <TICKERS> --template consensus.json`,
                                  ask the user to fill it, then pass --consensus consensus.json
         user chose "skip"?   -> leave NTM blank; workbook is complete on the LTM side
```
Always footnote the consensus provider + as-of date. If blank, the workbook prints a gold
"NOT PROVIDED — requires a consensus-data login" note per name.

## Branch: missing / non-standard line items (per company)
- **No `LongTermDebtNoncurrent`** → try `LongTermDebt` / `LongTermDebtAndCapitalLeaseObligations`;
  if still missing, flag and ask the analyst to confirm against the 10-Q.
- **No finance lease tag** → treat as $0 and flag (many issuers have none).
- **No minority interest** → $0 (most issuers have none) — not an error.
- **No `AssetsCurrent` / `LiabilitiesCurrent`** (banks, insurers, some REITs use an UNCLASSIFIED
  balance sheet) → working-capital adjustment can't be computed. Omit it, flag prominently, and
  warn the user the house EV definition is a poor fit (see the financials/alts branch below and
  `reference/financials_and_alts.md`).
- **Foreign private issuer** (20-F/40-F, no 10-Q/10-K) → out of scope; surface to the user.
- **Negative denominator** (e.g., negative EBITDA) → multiple shows `nm` (not meaningful).

## Branch: dual-class / multi-class / Up-C issuers
If shares trade under multiple classes (GOOGL/GOOG, BRK.A/BRK.B, FOX/FOXA) or the issuer uses an
Up-C structure (most alt managers — BX, KKR, ARES, OWL), the XBRL default share series is often
class-split or stale and the engine returns shares = `None` (flagged).
- Get the current **Class A** count from the 10-Q cover (or `fetch_earnings.py`) and pass it in:
  `build_comps.py <TICKERS> --shares "OWL=675802413,ARES=222028421"`. The engine uses it for market
  cap and footnotes that, for Up-C names, **total economic value also includes operating-group units
  (NCI)** — so report an economic market cap (Class A + units) too.
- Multi-traded-class (no Up-C): market equity = Σ (class shares × class price); sum all classes.
- Confirm handling in intake; footnote the split.

## Branch: financials / alternative asset managers (WRONG TOOL — switch frameworks)
If the engine flags `is_financial` (no classified balance sheet AND no operating income), or the name
is a bank / insurer / **alternative asset manager** (BX, KKR, ARES, OWL, APO, CG, TPG, BAM, …):
- EV/EBITDA and the working-capital EV definition do **not** apply. Do not force them.
- **Banks/insurers** → P/E, P/TBV, P/B.
- **Alt managers** → value on AUM, **Fee-Related Earnings (FRE)**, **Distributable Earnings** (P/E,
  P/FRE, P/Distributable, mkt cap/AUM). Pull AUM/FRE/DE from the quarterly **earnings release**
  (`fetch_earnings.py`), then build with `alt_manager_comp.py: render(data, out)`.
- **See [`reference/financials_and_alts.md`](reference/financials_and_alts.md)** for the full
  playbook (recognition, metrics, sources, formulas, worked OWL/ARES/BX/KKR precedent).
- Tell the user plainly why EV/EBITDA doesn't fit and offer the right comp.

## Branch: fiscal-year edge cases
- If the latest filing is a **10-K** (no newer 10-Q), LTM = the fiscal-year figure (handled by
  `company_facts.compute_ltm`).
- If a 10-Q YTD or prior-year YTD can't be matched cleanly, the engine degrades to FY and emits a
  `warn`; review it in QA.
