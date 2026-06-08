# Phase 03 — Market data (latest price)

Get the latest close for each ticker. **Fast path:** handled inside `build_comps.py`.

By hand: `python assets/market_price.py <TICKERS>` → Yahoo Finance chart API (keyless), with stooq
and a Chrome/manual fallback. Returns price, as-of timestamp, currency, source.

**Watch for:**
- `fallback_needed: true` → Yahoo + stooq both failed. Open `finance.yahoo.com/quote/<TICKER>` in
  Chrome and read the last price, or ask the user to paste it. Footnote source + timestamp. Never
  recall a price from memory or round.
- Markets closed (weekend/holiday) → most recent close is correct; footnote the date.
- Dual-class → fetch each class's price; market equity sums classes (see [router.md](../router.md)).
- Non-USD listings → note currency; keep the comp set in one currency.
