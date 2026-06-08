#!/usr/bin/env python3
"""
fetch_earnings.py — Pull a company's latest quarterly EARNINGS RELEASE (8-K, Exhibit 99.x) from SEC
EDGAR. No login. Two uses:
  1) Alternative asset managers / financials: their key metrics (AUM, Fee-Related Earnings,
     Distributable Earnings, per-share figures) live in the earnings release, NOT in standard XBRL.
     See reference/financials_and_alts.md.
  2) Phase 06 cross-check: the release is also the source for company-reported "Adjusted EBITDA",
     guidance, etc. to reconcile against our clean computed figures.

Functions:
  latest_earnings_8k(cik, subs) -> (accession, filingDate)         # most recent 8-K w/ item 2.02
  exhibit_texts(cik, accession) -> {filename: stripped_text}        # all .htm exhibits, tag-stripped
  get_earnings(ticker, cache_dir) -> {ticker, accession, date, files, text}
  grep(text, term, window=240, maxhits=3) -> [context strings]      # eyeball figures in the text

CLI:
  python fetch_earnings.py KKR --grep "Fee Related Earnings" "Assets Under Management"
"""
import argparse, json, os, re, sys
import fetch_edgar as fe

HERE = os.path.dirname(os.path.abspath(__file__))


def _strip(html):
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&#160;|&nbsp;|&#8217;|&#8211;|&#8212;|&amp;|&#8195;|&#8194;|&#8201;|&#9;|&#150;|&#167;|&#8226;|&#8220;|&#8221;", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def latest_earnings_8k(cik, subs):
    r = subs["filings"]["recent"]
    n = len(r["accessionNumber"])
    items = r.get("items", [""] * n)
    for i in range(n):
        if r["form"][i] == "8-K" and "2.02" in (items[i] or ""):
            return r["accessionNumber"][i], r["filingDate"][i]
    # fall back to the most recent 8-K of any kind
    for i in range(n):
        if r["form"][i] == "8-K":
            return r["accessionNumber"][i], r["filingDate"][i]
    return None, None


def exhibit_texts(cik, accession, max_chars=200000):
    accn = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}"
    idx = json.loads(fe._get(f"{base}/index.json").decode("utf-8", "replace"))
    out = {}
    for f in idx["directory"]["item"]:
        name = f["name"]
        if name.lower().endswith((".htm", ".html")) and "index" not in name.lower():
            try:
                out[name] = _strip(fe._get(f"{base}/{name}").decode("utf-8", "replace"))[:max_chars]
            except Exception as e:
                out[name] = f"<fetch error: {e}>"
    return out


def get_earnings(ticker, cache_dir):
    meta = fe.fetch_ticker(ticker, cache_dir)
    subs = fe.get_submissions(meta["cik"], cache_dir)
    acc, date = latest_earnings_8k(meta["cik"], subs)
    if not acc:
        return {"ticker": ticker.upper(), "error": "no 8-K found"}
    texts = exhibit_texts(meta["cik"], acc)
    return {"ticker": ticker.upper(), "cik": meta["cik"], "accession": acc, "date": date,
            "files": list(texts.keys()), "text": "  ".join(texts.values()), "by_file": texts}


def grep(text, term, window=240, maxhits=3):
    out, seen = [], []
    for m in re.finditer(re.escape(term), text, re.I):
        if all(abs(m.start() - s) > 250 for s in seen):
            out.append(text[max(0, m.start() - 80):m.start() + window])
            seen.append(m.start())
        if len(out) >= maxhits:
            break
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--out", default=os.path.join(HERE, "_cache"))
    ap.add_argument("--grep", nargs="*", default=["Assets Under Management", "Fee Related Earnings",
                                                  "Distributable Earnings", "per share"])
    args = ap.parse_args(argv)
    e = get_earnings(args.ticker, args.out)
    print(f"{e['ticker']} 8-K {e.get('accession')} filed {e.get('date')}")
    print("exhibits:", e.get("files"))
    for term in args.grep:
        for ctx in grep(e.get("text", ""), term):
            print(f"  [{term}] ...{ctx}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
