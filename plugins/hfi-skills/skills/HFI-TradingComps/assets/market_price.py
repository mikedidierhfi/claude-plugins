#!/usr/bin/env python3
"""
market_price.py — Latest stock price (most recent close) with NO login required.

Primary source: Yahoo Finance chart JSON (keyless, browser UA).
  https://query1.finance.yahoo.com/v8/finance/chart/AAPL?interval=1d&range=5d
  -> chart.result[0].meta.regularMarketPrice / regularMarketTime / currency / previousClose
Secondary: stooq.com CSV (often bot-walled now; tried only if Yahoo fails).
Documented fallback (see phases/03_market_data.md): drive Chrome to read the last price from
finance.yahoo.com or google.com/finance, or prompt the user to paste it. NEVER hard-code or
recall a price from memory.

Usage:
  python market_price.py AAPL MSFT BRK-B
"""
import argparse, csv, datetime as dt, io, json, time, urllib.request, urllib.error

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
YAHOO_HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]


def _get(url, timeout=20, retries=3, backoff=1.5):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/csv,*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, urllib.error.HTTPError) as e:
            last = e
            time.sleep(backoff * (i + 1))
    raise RuntimeError(str(last))


def _yahoo_symbol(ticker):
    # Yahoo uses dashes for share classes: BRK.B -> BRK-B
    return ticker.upper().strip().replace(".", "-")


def get_price_yahoo(ticker):
    sym = _yahoo_symbol(ticker)
    last_err = None
    for host in YAHOO_HOSTS:
        url = f"https://{host}/v8/finance/chart/{sym}?interval=1d&range=5d"
        try:
            d = json.loads(_get(url))
            res = (d.get("chart", {}).get("result") or [None])[0]
            if not res:
                last_err = "empty result"; continue
            m = res.get("meta", {})
            price = m.get("regularMarketPrice")
            if price is None:
                last_err = "no regularMarketPrice"; continue
            ts = m.get("regularMarketTime")
            as_of = dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else None
            return {
                "ticker": ticker.upper(), "price": float(price),
                "as_of": as_of, "currency": m.get("currency"),
                "exchange": m.get("exchangeName"),
                "previous_close": m.get("chartPreviousClose") or m.get("previousClose"),
                "source": "Yahoo Finance chart API (keyless)",
                "source_url": url,
            }
        except Exception as e:
            last_err = repr(e)
    return {"ticker": ticker.upper(), "price": None, "error": f"yahoo failed: {last_err}"}


def get_price_stooq(ticker):
    url = f"https://stooq.com/q/l/?s={ticker.lower().strip()}.us&f=sd2t2ohlcv&h&e=csv"
    text = _get(url)
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return {"ticker": ticker.upper(), "price": None, "error": "stooq no rows"}
    close = (rows[0].get("Close") or "").strip()
    if not close or close.upper() == "N/D" or "<" in text[:20]:
        return {"ticker": ticker.upper(), "price": None, "error": "stooq unavailable/bot-walled"}
    try:
        return {"ticker": ticker.upper(), "price": float(close), "as_of": rows[0].get("Date"),
                "source": "stooq.com (keyless)", "source_url": url}
    except ValueError:
        return {"ticker": ticker.upper(), "price": None, "error": f"stooq parse {close!r}"}


def get_price(ticker):
    r = get_price_yahoo(ticker)
    if r.get("price") is not None:
        return r
    try:
        s = get_price_stooq(ticker)
        if s.get("price") is not None:
            return s
    except Exception:
        pass
    return {"ticker": ticker.upper(), "price": None, "error": r.get("error"),
            "fallback_needed": True,
            "fallback_hint": "Use Chrome to read the last close from finance.yahoo.com/quote/<TICKER> "
                             "or google.com/finance, or ask the user to paste the price."}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    args = ap.parse_args(argv)
    out = []
    for i, t in enumerate(args.tickers):
        if i:
            time.sleep(0.2)
        out.append(get_price(t))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
