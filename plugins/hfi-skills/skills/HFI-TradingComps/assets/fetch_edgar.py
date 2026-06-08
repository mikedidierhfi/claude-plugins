#!/usr/bin/env python3
"""
fetch_edgar.py — Pull primary filing data for one or more tickers from SEC EDGAR.

No third-party dependencies (stdlib only). SEC's free JSON APIs:
  - Ticker -> CIK map:  https://www.sec.gov/files/company_tickers.json
  - Filing index:       https://data.sec.gov/submissions/CIK##########.json
  - XBRL company facts:  https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json

SEC requires a descriptive User-Agent with contact info. Override with env var SEC_UA.

Usage:
  python fetch_edgar.py AAPL MSFT --out ./_cache
  python fetch_edgar.py AAPL --summary        # print latest 10-Q/10-K summary as JSON

Caches the big companyfacts/submissions JSON to --out so downstream parsers reuse them.
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

SEC_UA = os.environ.get(
    "SEC_UA",
    "HFI-TradingComps skill (SEC EDGAR fair access; set SEC_UA env var to your name+email)",
)
TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"


def _get(url, retries=4, backoff=1.5, timeout=30):
    last = None
    for i in range(retries):
        try:
            # urllib doesn't auto-gunzip; ask for identity encoding to keep parsing simple/robust
            req = urllib.request.Request(url, headers={
                "User-Agent": SEC_UA,
                "Accept-Encoding": "identity",
                "Accept": "application/json,text/plain,*/*",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429, 500, 502, 503, 504):
                time.sleep(backoff * (i + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(backoff * (i + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} ({last})")


def _get_json(url, **kw):
    return json.loads(_get(url, **kw).decode("utf-8"))


_TICKER_MAP = None
def load_ticker_map(cache_dir):
    global _TICKER_MAP
    if _TICKER_MAP is not None:
        return _TICKER_MAP
    path = os.path.join(cache_dir, "company_tickers.json")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path) < 7 * 86400):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = _get_json(TICKER_MAP_URL)
        os.makedirs(cache_dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    # data is {"0": {"cik_str":320193,"ticker":"AAPL","title":"Apple Inc."}, ...}
    m = {}
    for row in data.values():
        m[row["ticker"].upper()] = {"cik": int(row["cik_str"]), "title": row["title"]}
    _TICKER_MAP = m
    return m


def resolve_cik(ticker, cache_dir):
    m = load_ticker_map(cache_dir)
    t = ticker.upper().strip()
    if t in m:
        return m[t]
    # try dotted/dashed share-class variants (BRK.B <-> BRK-B)
    for alt in (t.replace(".", "-"), t.replace("-", "."), t.split(".")[0], t.split("-")[0]):
        if alt in m:
            return m[alt]
    raise KeyError(f"Ticker not found in SEC map: {ticker}")


def cik10(cik):
    return str(int(cik)).zfill(10)


def get_submissions(cik, cache_dir):
    path = os.path.join(cache_dir, f"submissions_CIK{cik10(cik)}.json")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path) < 86400):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    data = _get_json(SUBMISSIONS_URL.format(cik10=cik10(cik)))
    os.makedirs(cache_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def get_companyfacts(cik, cache_dir):
    path = os.path.join(cache_dir, f"companyfacts_CIK{cik10(cik)}.json")
    if os.path.exists(path) and (time.time() - os.path.getmtime(path) < 86400):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    data = _get_json(COMPANYFACTS_URL.format(cik10=cik10(cik)))
    os.makedirs(cache_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def latest_filings(submissions, forms=("10-Q", "10-K")):
    """Return {form: {accession, filingDate, reportDate, primaryDocument, url}} for the most
    recent of each form."""
    recent = submissions.get("filings", {}).get("recent", {})
    cols = ["accessionNumber", "filingDate", "reportDate", "form", "primaryDocument"]
    rows = list(zip(*[recent.get(c, []) for c in cols]))
    out = {}
    cik = submissions.get("cik")
    for acc, fdate, rdate, form, doc in rows:
        if form in forms and form not in out:
            acc_nodash = acc.replace("-", "")
            out[form] = {
                "accession": acc,
                "filingDate": fdate,
                "reportDate": rdate,
                "primaryDocument": doc,
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{doc}",
                "index_url": f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik10(cik)}&type={form}",
            }
        if all(f in out for f in forms):
            break
    return out


def fetch_ticker(ticker, cache_dir):
    info = resolve_cik(ticker, cache_dir)
    cik = info["cik"]
    subs = get_submissions(cik, cache_dir)
    facts = get_companyfacts(cik, cache_dir)
    latest = latest_filings(subs)
    n_concepts = sum(len(v) for v in facts.get("facts", {}).values())
    return {
        "ticker": ticker.upper(),
        "cik": cik,
        "cik10": cik10(cik),
        "title": info["title"],
        "fiscalYearEnd": subs.get("fiscalYearEnd"),
        "exchange": (subs.get("exchanges") or [None])[0],
        "latest_10Q": latest.get("10-Q"),
        "latest_10K": latest.get("10-K"),
        "n_xbrl_concepts": n_concepts,
        "companyfacts_cache": os.path.join(cache_dir, f"companyfacts_CIK{cik10(cik)}.json"),
        "submissions_cache": os.path.join(cache_dir, f"submissions_CIK{cik10(cik)}.json"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fetch SEC EDGAR primary data for tickers.")
    ap.add_argument("tickers", nargs="+", help="Ticker symbols, e.g. AAPL MSFT")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "_cache"),
                    help="Cache directory for downloaded JSON")
    ap.add_argument("--summary", action="store_true", help="Print summary JSON (default true)")
    args = ap.parse_args(argv)

    results = []
    for i, t in enumerate(args.tickers):
        if i:
            time.sleep(0.3)  # be polite to SEC
        try:
            results.append(fetch_ticker(t, args.out))
        except Exception as e:
            results.append({"ticker": t.upper(), "error": str(e)})
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
