#!/usr/bin/env python3
"""
fmp_consensus.py — Optional NTM (Next-Twelve-Months) Wall Street consensus via Financial Modeling
Prep (FMP), a low-cost keyed API. Used when consensus_mode='fmp'.

SECURITY: the API key is read from the environment or a local config file in the user's HOME —
it is NEVER hard-coded here and must never be committed. Resolution order:
    1. FMP_API_KEY environment variable
    2. ~/.hfi-tradingcomps.json   ->   {"fmp_api_key": "..."}

FMP's analyst-estimates (stable API) returns ANNUAL consensus for revenue / EBITDA / EBIT / net
income (there is no CFO estimate, so NTM CFO stays blank — same gap as CapIQ's thin IQ_CFO_EST).
We CALENDARIZE annual estimates into a true next-twelve-months figure by time-weighting the current
and next fiscal-year estimates:

    NTM = f * FY1 + (1 - f) * FY2,   f = (FY1_fiscal_year_end - today) / 365   (clamped to [0, 1])

All outputs are in $ MILLIONS, matching the consensus schema in consensus_input.py.
"""
import datetime as dt
import json
import os
import urllib.request

STABLE_URL = "https://financialmodelingprep.com/stable/analyst-estimates"
CONFIG_PATH = os.path.expanduser("~/.hfi-tradingcomps.json")
UA = "hfi-tradingcomps/1.0 (SEC primary-source comps; contact analyst)"


def get_key():
    """FMP_API_KEY env var, else ~/.hfi-tradingcomps.json {'fmp_api_key': ...}, else None."""
    k = (os.environ.get("FMP_API_KEY") or "").strip()
    if k:
        return k
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return ((json.load(f) or {}).get("fmp_api_key") or "").strip() or None
    except Exception:
        return None


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _d(s):
    return dt.date.fromisoformat(str(s)[:10])


def ntm_for(symbol, key, as_of=None, _fetch=None):
    """NTM consensus record (in $mm) for one symbol, or None if unavailable. `_fetch` is an injection
    point for offline tests (returns the raw FMP annual-estimates list)."""
    today = dt.date.fromisoformat(as_of) if as_of else dt.date.today()
    # No `limit` param: FMP's free tier rejects limit>~10 (HTTP 402), and the default response already
    # returns a ~10-row window spanning recent history through several forward years — which always
    # includes the current and next fiscal year (FY1/FY2) we calendarize from.
    fetch = _fetch or (lambda: _get(
        f"{STABLE_URL}?symbol={symbol}&period=annual&apikey={key}"))
    recs = fetch()
    if not isinstance(recs, list) or not recs:
        return None
    fut = sorted((r for r in recs if r.get("date") and _d(r["date"]) >= today),
                 key=lambda r: r["date"])
    if not fut:
        return None
    fy1 = fut[0]
    fy2 = fut[1] if len(fut) > 1 else None
    f = max(0.0, min(1.0, (_d(fy1["date"]) - today).days / 365.0))

    def blend(field):
        v1 = fy1.get(field)
        if not isinstance(v1, (int, float)):
            return None
        if fy2 is None:
            return float(v1)
        v2 = fy2.get(field)
        if not isinstance(v2, (int, float)):
            return float(v1)
        return f * v1 + (1.0 - f) * v2

    def mm(x):
        return (x / 1_000_000.0) if isinstance(x, (int, float)) else None

    eb, ei, ni = mm(blend("ebitdaAvg")), mm(blend("ebitAvg")), mm(blend("netIncomeAvg"))
    if eb is None and ei is None and ni is None:
        return None
    y1 = _d(fy1["date"]).year
    src = f"FMP analyst consensus (calendarized NTM: {f:.0%} FY{y1}"
    src += (f" / {1 - f:.0%} FY{_d(fy2['date']).year})" if fy2 else ")")
    return {
        "ntm_ebitda": eb, "ntm_ebit": ei, "ntm_cfo": None, "ntm_net_income": ni,
        "ntm_revenue": mm(blend("revenueAvg")),
        "source": src, "as_of": today.isoformat(),
    }


def fetch_ntm(tickers, key, as_of=None):
    """{TICKER: record-or-None} for all tickers; per-ticker failures degrade to None (never raises)."""
    out = {}
    for t in tickers:
        T = t.upper()
        try:
            out[T] = ntm_for(T, key, as_of=as_of)
        except Exception:
            out[T] = None
    return out


def main(argv=None):
    import argparse
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--as-of", help="YYYY-MM-DD (default: today)")
    args = ap.parse_args(argv)
    key = get_key()
    if not key:
        print("No FMP key. Set FMP_API_KEY or ~/.hfi-tradingcomps.json {\"fmp_api_key\": \"...\"}.")
        return 1
    print(json.dumps(fetch_ntm(args.tickers, key, as_of=args.as_of), indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
