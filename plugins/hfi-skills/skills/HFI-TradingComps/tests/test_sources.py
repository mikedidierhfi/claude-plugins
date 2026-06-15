#!/usr/bin/env python3
"""
test_sources.py — Offline test for sources_report.build_sources_markdown (the chat "Sources &
citations" block). Uses a synthetic comps dict with with_statement_links=False (no network) and
asserts the block contains the EDGAR filings link, the price source link, the filing-index links
+ accessions, and per-figure XBRL citations + the LTM bridge breakdown.
Run: python tests/test_sources.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import sources_report as sr  # noqa: E402


def _cite(tag, form, end, accn):
    return {"tag": tag, "form": form, "end": end, "accn": accn, "start": None}


COMPS = {
    "tickers": ["AAPL", "NOPX"],
    "companies": {
        "AAPL": {
            "cik": 320193, "title": "Apple Inc.",
            "price": 296.14, "price_as_of": "2026-06-05", "price_source": "Yahoo Finance chart API",
            "price_source_url": "https://query1.finance.yahoo.com/v8/finance/chart/AAPL",
            "filing_10q": {"reportDate": "2026-03-28", "filingDate": "2026-05-01",
                           "accession": "0000320193-26-000050", "url": "https://www.sec.gov/.../10q-index.htm"},
            "filing_10k": {"reportDate": "2025-09-27", "filingDate": "2025-10-31",
                           "accession": "0000320193-25-000099", "url": "https://www.sec.gov/.../10k-index.htm"},
            "citations": {
                "shares_outstanding": _cite("dei:EntityCommonStockSharesOutstanding", "10-Q", "2026-03-28", "0000320193-26-000050"),
                "long_term_debt_noncurrent": _cite("us-gaap:LongTermDebtNoncurrent", "10-Q", "2026-03-28", "0000320193-26-000050"),
            },
            "ltm_components": {
                "net_income": {"fy": _cite("us-gaap:NetIncomeLoss", "10-K", "2025-09-27", "k"),
                               "ytd": _cite("us-gaap:NetIncomeLoss", "10-Q", "2026-03-28", "q"),
                               "prior_ytd": _cite("us-gaap:NetIncomeLoss", "10-Q", "2025-03-29", "q0")},
            },
        },
        # a company with no price / no citations -> must not crash, still emits a section
        "NOPX": {"cik": 999999, "title": "No Price Co", "price": None,
                 "filing_10q": {}, "filing_10k": {}, "citations": {}, "ltm_components": {}},
    },
}


def run():
    fails = []

    def ck(name, cond):
        if not cond:
            fails.append("  FAIL " + name)

    md = sr.build_sources_markdown(COMPS, with_statement_links=False)

    ck("has header", "## Sources & citations" in md)
    ck("AAPL section present", "### AAPL — Apple Inc." in md)
    ck("EDGAR all-filings link w/ CIK", "CIK=320193" in md and "browse-edgar" in md)
    ck("price source link", "query1.finance.yahoo.com" in md and "**Price:**" in md)
    ck("10-Q filing index link + accession", "0000320193-26-000050" in md and "[filing index]" in md)
    ck("10-K present", "0000320193-25-000099" in md)
    ck("line-item XBRL citation present", "us-gaap:LongTermDebtNoncurrent" in md)
    ck("shares citation present", "dei:EntityCommonStockSharesOutstanding" in md)
    ck("LTM bridge breakdown present", "LTM bridge" in md and "prior-YTD" in md)
    ck("no-price company doesn't crash + still sectioned", "### NOPX — No Price Co" in md)
    ck("no spurious price line for no-price co", md.count("**Price:**") == 1)

    print("-" * 56)
    print(f"{11 - len(fails)}/11 passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
