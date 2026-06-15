#!/usr/bin/env python3
"""
test_price.py — Offline tests for market_price.py (the price layer was previously untested).

Monkeypatches the single network entry point (market_price._get) with canned provider payloads, so
parsing and the multi-provider fallback chain (Yahoo -> CNBC -> stooq -> manual) are exercised with
no network and deterministic results. Run: python tests/test_price.py
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import market_price as mp  # noqa: E402

YAHOO_JSON = json.dumps({"chart": {"result": [{"meta": {
    "regularMarketPrice": 123.45, "regularMarketTime": 1_700_000_000,
    "currency": "USD", "exchangeName": "NMS", "chartPreviousClose": 120.0}}]}})
CNBC_JSON = json.dumps({"QuickQuoteResult": {"QuickQuote": [{
    "last": "234.56", "last_time": "2026-06-12T20:00:00.000-0400", "currencyCode": "USD"}]}})
STOOQ_CSV = "Symbol,Date,Time,Open,High,Low,Close,Volume\nAAPL.US,2026-06-12,22:00:05,340,346,339,345.67,1000000\n"


def fake_get(only=None):
    """Return a _get stub. `only` = set of providers allowed to 'succeed'; others raise (simulate
    outage/bot-wall) so the fallback chain can be tested."""
    allow = only if only is not None else {"yahoo", "cnbc", "stooq"}

    def _get(url, timeout=20, retries=3, backoff=1.5):
        if "finance.yahoo.com" in url:
            if "yahoo" in allow:
                return YAHOO_JSON
            raise RuntimeError("yahoo down")
        if "cnbc.com" in url:
            if "cnbc" in allow:
                return CNBC_JSON
            raise RuntimeError("cnbc down")
        if "stooq.com" in url:
            if "stooq" in allow:
                return STOOQ_CSV
            return "<html>bot wall</html>"
        raise RuntimeError("unexpected url " + url)
    return _get


def run():
    fails = []

    def ck(name, cond):
        if not cond:
            fails.append("  FAIL " + name)

    # symbol mapping (no network)
    ck("yahoo symbol BRK.B -> BRK-B", mp._yahoo_symbol("BRK.B") == "BRK-B")

    # individual providers parse correctly
    mp._get = fake_get()
    y = mp.get_price_yahoo("AAPL")
    ck("yahoo price parsed", y.get("price") == 123.45)
    ck("yahoo currency parsed", y.get("currency") == "USD")
    ck("yahoo as_of derived", bool(y.get("as_of")))

    c = mp.get_price_cnbc("AAPL")
    ck("cnbc price parsed", c.get("price") == 234.56)
    ck("cnbc source labeled", "CNBC" in (c.get("source") or ""))

    s = mp.get_price_stooq("AAPL")
    ck("stooq price parsed", s.get("price") == 345.67)

    # fallback chain
    mp._get = fake_get(only={"yahoo", "cnbc", "stooq"})
    ck("get_price prefers Yahoo", mp.get_price("AAPL").get("price") == 123.45)

    mp._get = fake_get(only={"cnbc", "stooq"})           # Yahoo down
    r = mp.get_price("AAPL")
    ck("falls back to CNBC when Yahoo down", r.get("price") == 234.56)

    mp._get = fake_get(only={"stooq"})                   # Yahoo + CNBC down
    r = mp.get_price("AAPL")
    ck("falls back to stooq when Yahoo+CNBC down", r.get("price") == 345.67)

    mp._get = fake_get(only=set())                       # everything down
    r = mp.get_price("AAPL")
    ck("all-fail -> price None", r.get("price") is None)
    ck("all-fail -> fallback_needed", r.get("fallback_needed") is True)
    ck("all-fail -> error lists every provider tried",
       all(k in (r.get("error") or "") for k in ("yahoo", "cnbc", "stooq")))

    print("-" * 56)
    print(f"{14 - len(fails)}/14 passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
