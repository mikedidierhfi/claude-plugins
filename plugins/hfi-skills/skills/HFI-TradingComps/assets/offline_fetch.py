#!/usr/bin/env python3
"""
offline_fetch.py — NO-EGRESS fallback for chat/Cowork sandboxes that can't reach data.sec.gov from
Python. Instead of one multi-MB companyfacts/submissions file, it uses EDGAR's PER-CONCEPT endpoint
(small JSON, web-fetch friendly). The agent fetches each small URL with its web/browser tool and
saves the response; this module assembles them into the exact `_cache/` files the normal pipeline
reads — so build_comps.py then runs fully offline. Filing dates are derived from the concept data
itself, so no `submissions` download is needed.

Workflow (run by the agent when `selfcheck.py` shows EDGAR is NOT reachable):
  1. Get the company's CIK (e.g., web_fetch the tiny atom:
     https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&ticker=AAPL&type=10-K&count=1&output=atom )
  2. python3 assets/offline_fetch.py plan AAPL 320193
        -> prints the ~30 small concept URLs + the filename to save each response as.
  3. web_fetch each URL; save the JSON into a folder (default _cache/concepts_<TICKER>/).
  4. python3 assets/offline_fetch.py assemble AAPL 320193
        -> writes _cache/companyfacts_CIK##########.json + _cache/submissions_CIK##########.json
           + ensures the ticker->CIK map entry.
  5. python3 assets/build_comps.py AAPL --prices "AAPL=<price>" --xlsx out.xlsx   (price fetched via web tool)
"""
import argparse, json, os, sys
import fetch_edgar as fe

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "xbrl_tags.json"), "r", encoding="utf-8") as _f:
    TAGS = json.load(_f)
CC_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{cik10}/{tax}/{tag}.json"


def needed_concepts():
    out = []
    for spec in TAGS.values():
        if isinstance(spec, dict) and "tags" in spec:
            for t in spec["tags"]:
                pair = (t["taxonomy"], t["tag"])
                if pair not in out:
                    out.append(pair)
    return out


def _save_name(tax, tag):
    return f"concept_{tax}_{tag}.json"


def plan(cik, ticker):
    c10 = fe.cik10(cik)
    print(f"# Fetch these {len(needed_concepts())} small JSON files for {ticker.upper()} (CIK {c10})")
    print(f"# Save each into:  _cache/concepts_{ticker.upper()}/<save_as>")
    print(f"# A 404 on a concept just means the issuer doesn't report it — skip it, that's fine.\n")
    for tax, tag in needed_concepts():
        print(f"{CC_URL.format(cik10=c10, tax=tax, tag=tag)}\t-> {_save_name(tax, tag)}")


def assemble(cik, ticker, concept_dir, cache_dir):
    facts = {"cik": int(cik), "entityName": ticker.upper(), "facts": {}}
    found = 0
    for tax, tag in needed_concepts():
        path = os.path.join(concept_dir, _save_name(tax, tag))
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            try:
                cc = json.load(f)
            except Exception:
                continue
        units = cc.get("units")
        if not units:
            continue
        facts["facts"].setdefault(tax, {})[tag] = {"label": cc.get("label"), "units": units}
        found += 1

    if found == 0:
        raise SystemExit(f"No concept files found in {concept_dir} — run 'plan' and fetch them first.")

    os.makedirs(cache_dir, exist_ok=True)
    cf_path = os.path.join(cache_dir, f"companyfacts_CIK{fe.cik10(cik)}.json")
    with open(cf_path, "w", encoding="utf-8") as f:
        json.dump(facts, f)

    subs = _derive_submissions(cik, ticker, facts)
    subs_path = os.path.join(cache_dir, f"submissions_CIK{fe.cik10(cik)}.json")
    with open(subs_path, "w", encoding="utf-8") as f:
        json.dump(subs, f)

    _ensure_ticker_map(cache_dir, ticker, cik)

    q = subs["filings"]["recent"]
    forms = list(zip(q["form"], q["reportDate"], q["accessionNumber"]))
    print(json.dumps({"ticker": ticker.upper(), "cik": int(cik), "concepts_assembled": found,
                      "companyfacts_cache": cf_path, "submissions_cache": subs_path,
                      "latest_filings": forms}, indent=2))


def _derive_submissions(cik, ticker, facts):
    """Find the latest 10-Q and 10-K period-ends from the concept facts themselves (each fact carries
    form/end/accn/filed), so we don't need the big submissions file."""
    rows = []
    for tax, concepts in facts["facts"].items():
        if tax == "dei":
            continue  # cover-page facts (e.g. shares o/s) carry the filing/cover date, not the period-end
        for tag, node in concepts.items():
            for unit, recs in node.get("units", {}).items():
                for r in recs:
                    if r.get("form") in ("10-Q", "10-K") and r.get("end"):
                        rows.append((r["form"], r["end"], r.get("filed", ""), r.get("accn", "")))
    recent = {"accessionNumber": [], "filingDate": [], "reportDate": [], "form": [],
              "primaryDocument": [], "items": []}
    for form in ("10-Q", "10-K"):
        cand = [x for x in rows if x[0] == form]
        if not cand:
            continue
        cand.sort(key=lambda x: (x[1], x[2]))  # by period-end, then filed
        f, end, filed, accn = cand[-1]
        recent["accessionNumber"].append(accn)
        recent["filingDate"].append(filed)
        recent["reportDate"].append(end)
        recent["form"].append(form)
        recent["primaryDocument"].append("")  # unknown offline -> latest_filings yields the folder URL
        recent["items"].append("")
    return {"cik": int(cik), "entityName": ticker.upper(), "fiscalYearEnd": "",
            "exchanges": [None], "filings": {"recent": recent}}


def _ensure_ticker_map(cache_dir, ticker, cik):
    path = os.path.join(cache_dir, "company_tickers.json")
    data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data[ticker.upper()] = {"cik_str": int(cik), "ticker": ticker.upper(), "title": ticker.upper()}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def main(argv=None):
    ap = argparse.ArgumentParser(description="No-egress EDGAR fallback (per-concept fetch + assemble).")
    ap.add_argument("mode", choices=["plan", "assemble"])
    ap.add_argument("ticker")
    ap.add_argument("cik")
    ap.add_argument("--concept-dir", default=None)
    ap.add_argument("--out", default=fe.DEFAULT_CACHE)
    args = ap.parse_args(argv)
    cdir = args.concept_dir or os.path.join(args.out, f"concepts_{args.ticker.upper()}")
    if args.mode == "plan":
        os.makedirs(cdir, exist_ok=True)
        plan(args.cik, args.ticker)
    else:
        assemble(args.cik, args.ticker, cdir, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
