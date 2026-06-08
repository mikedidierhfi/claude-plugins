#!/usr/bin/env python3
"""
test_offline.py — Verifies the NO-EGRESS fallback (offline_fetch.py) produces the SAME results as
the direct path. Simulates the agent's per-concept web-fetches by splitting the frozen AAPL
companyfacts fixture into per-concept files, assembles them, derives the filing dates, and confirms
the line items + LTM match the validated anchors exactly. Run: python tests/test_offline.py
"""
import contextlib, io, json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, ASSETS)
import offline_fetch as off
import company_facts as cf
import fetch_edgar as fe

CIK = 320193  # Apple


def run():
    fails, n = [], [0]

    def ck(name, cond):
        n[0] += 1
        if not cond:
            fails.append("  FAIL " + name)

    with open(os.path.join(FIX, "AAPL.json"), "r", encoding="utf-8") as f:
        facts = json.load(f)

    tmp = tempfile.mkdtemp()
    cdir = os.path.join(tmp, "concepts"); os.makedirs(cdir)
    cache = os.path.join(tmp, "cache"); os.makedirs(cache)

    # Simulate the agent's small per-concept web-fetches: one companyconcept-shaped file per concept
    for tax, concepts in facts["facts"].items():
        for tag, node in concepts.items():
            cc = {"cik": CIK, "taxonomy": tax, "tag": tag, "label": node.get("label"),
                  "units": node.get("units", {})}
            with open(os.path.join(cdir, off._save_name(tax, tag)), "w", encoding="utf-8") as f:
                json.dump(cc, f)

    with contextlib.redirect_stdout(io.StringIO()):  # assemble prints a summary; keep test output clean
        off.assemble(CIK, "AAPL", cdir, cache)

    afacts = json.load(open(os.path.join(cache, f"companyfacts_CIK{fe.cik10(CIK)}.json"), encoding="utf-8"))
    asubs = json.load(open(os.path.join(cache, f"submissions_CIK{fe.cik10(CIK)}.json"), encoding="utf-8"))
    latest = fe.latest_filings(asubs)
    q_end = (latest.get("10-Q") or {}).get("reportDate")
    fy_end = (latest.get("10-K") or {}).get("reportDate")

    # Dates derived from the concept data (not from a submissions download) must be the real period-ends
    ck("derived q_end = 2026-03-28 (not the cover date)", q_end == "2026-03-28")
    ck("derived fy_end = 2025-09-27", fy_end == "2025-09-27")

    r = cf.compute_line_items(afacts, q_end, fy_end, ticker="AAPL")
    ev = lambda k: r["ev_line_items"][k]["value"]
    ck("shares 14,687,356,000", ev("shares_outstanding") == 14_687_356_000)
    ck("LT debt 74,404,000,000", ev("long_term_debt_noncurrent") == 74_404_000_000)
    ck("current assets 144,114,000,000", ev("current_assets") == 144_114_000_000)
    ck("working capital 9,473,000,000", r["working_capital"] == 9_473_000_000)
    ck("LTM EBIT 147,366,000,000", r["ltm"]["operating_income_ebit"]["value"] == 147_366_000_000)
    ck("LTM EBITDA 159,976,000,000", r["ltm_ebitda_derived"] == 159_976_000_000)
    ck("LTM net income 122,575,000,000", r["ltm"]["net_income"]["value"] == 122_575_000_000)
    ck("LTM CFO 140,222,000,000", r["ltm"]["cfo"]["value"] == 140_222_000_000)

    tmap = json.load(open(os.path.join(cache, "company_tickers.json"), encoding="utf-8"))
    ck("ticker->CIK map entry written", any(v.get("ticker") == "AAPL" for v in tmap.values()))

    print("-" * 60)
    print(f"{n[0] - len(fails)}/{n[0]} passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
