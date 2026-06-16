#!/usr/bin/env python3
"""
test_render.py — Offline smoke test for the Excel renderer (build_comps_xlsx.render).

Builds a synthetic comps dict (no network) and asserts the workbook renders with the right shape:
live derived formulas, live =CIQ() NTM formulas (capiq_excel), static inputs carried, and manual
consensus written statically when provided. Run: python tests/test_render.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import openpyxl  # noqa: E402
import build_comps_xlsx as bx  # noqa: E402

OUT = os.path.join(HERE, "_out")
os.makedirs(OUT, exist_ok=True)


def _company(title, cik, ntm_provided=None):
    return {
        "title": title, "cik": cik, "is_financial": False,
        "filing_10q": {"reportDate": "2026-03-28", "filingDate": "2026-05-01", "accession": "x", "url": "u"},
        "filing_10k": {"reportDate": "2025-09-27", "filingDate": "2025-10-31", "accession": "y", "url": "u"},
        "price": 307.34, "price_as_of": "2026-06-05", "price_source": "Yahoo", "price_source_url": "u",
        "shares_mm": 14687.356, "market_equity_mm": None,
        "lt_debt_mm": 74404.0, "finance_lease_mm": 692.0, "minority_mm": None,
        "current_assets_mm": 144114.0, "current_liabilities_mm": 134641.0,
        "working_capital_mm": 9473.0, "cash_mm": 45572.0, "tev_mm": None,
        "ltm_mm": {"revenue": 451442.0, "ebit": 147366.0, "da": 12610.0,
                   "ebitda": 159976.0, "cfo": 140222.0, "net_income": 122575.0},
        "ntm_mm": ntm_provided or {"ebitda": None, "ebit": None, "cfo": None, "net_income": None},
        "ntm_source": None, "ntm_as_of": None, "ntm_provided": bool(ntm_provided),
        "multiples": {}, "pe_ltm": None, "citations": {}, "ltm_components": {}, "flags": ["test flag"],
    }


def _comps(mode, companies):
    return {
        "as_of_date": "2026-06-07", "currency": "USD",
        "units": "$ in millions; shares in millions; multiples in x",
        "methodology": "House EV = ...", "consensus_mode": mode,
        "tickers": list(companies.keys()), "companies": companies,
        "needs_consensus_for": [], "consensus_source_file": None,
    }


def all_values(path):
    wb = openpyxl.load_workbook(path)
    ws = wb.active
    return [str(c.value) for row in ws.iter_rows() for c in row if c.value is not None]


def run():
    fails = []

    # Case A: capiq_excel mode
    pA = os.path.join(OUT, "smoke_capiq.xlsx")
    bx.render(_comps("capiq_excel", {"AAPL": _company("Apple Inc.", 320193)}), pA)
    vA = all_values(pA)
    checks = {
        "renders & opens": len(vA) > 20,
        "live CIQ NTM formula present": any(s.startswith('=CIQ("AAPL","IQ_EBITDA_EST",IQ_NTM)') for s in vA),
        "derived formula present (ISNUMBER)": any("ISNUMBER" in s for s in vA),
        "TEV formula references N()": any(s.startswith("=IF(ISNUMBER(") and "N(" in s for s in vA),
        "multiple formula present": any('"nm"' in s and "/" in s for s in vA),
        "static price carried": any(s == "307.34" for s in vA),
        "static shares carried": any(s == "14687.356" for s in vA),
        "company title present": any("Apple Inc." in s for s in vA),
        "flag rendered": any("test flag" in s for s in vA),
    }
    for name, ok in checks.items():
        (fails.append(f"  FAIL capiq.{name}") if not ok else None)

    # Case B: manual mode with a provided NTM value -> static number, not a CIQ formula
    pB = os.path.join(OUT, "smoke_manual.xlsx")
    co = _company("Apple Inc.", 320193, ntm_provided={"ebitda": 175000.0, "ebit": None, "cfo": None, "net_income": None})
    bx.render(_comps("manual", {"AAPL": co}), pB)
    vB = all_values(pB)
    if not any(s == "175000.0" or s == "175000" for s in vB):
        fails.append("  FAIL manual.ntm_static_value_present")
    if any(s.startswith("=CIQ(") for s in vB):
        fails.append("  FAIL manual.should_not_have_CIQ_formulas")

    # Case C: the NTM source label must reflect the ACTUAL mode (regression — the workbook used to
    # always say "via Capital IQ" even when the data came from FMP).
    pC = os.path.join(OUT, "smoke_fmp.xlsx")
    bx.render(_comps("fmp", {"AAPL": _company("Apple Inc.", 320193)}), pC)
    vC = all_values(pC)
    if not any("via Financial Modeling Prep" in s for s in vC):
        fails.append("  FAIL fmp.source_label_names_FMP")
    if any("Capital IQ" in s for s in vC):
        fails.append("  FAIL fmp.must_not_mention_CapIQ")
    # and capiq mode must still name Capital IQ
    if not any("via Capital IQ" in s for s in vA):
        fails.append("  FAIL capiq.source_label_names_CapIQ")

    passed = (len(checks) + 5) - len(fails)
    print("-" * 56)
    print(f"{passed} passed, {len(fails)} failed")
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
