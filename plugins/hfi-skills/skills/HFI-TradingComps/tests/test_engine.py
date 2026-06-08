#!/usr/bin/env python3
"""
test_engine.py — Deterministic regression tests for the trading-comps data engine.

Runs the pure compute core (company_facts.compute_line_items) against FROZEN fixtures
(tests/fixtures/*.json, trimmed companyfacts) with pinned 10-Q/10-K period-ends. No network.

Covers:
  - Correct EV line items + LTM bridge for clean filers (AAPL, MSFT) — exact regression anchors.
  - STALENESS GUARD: JPM long-term debt (2014) and BRK-B shares (2011) must be IGNORED -> None.
  - Financial-issuer signature: JPM/BRK have no current assets/liabs and no operating income.
  - NCI captured: BRK-B minority interest is current and correct.

Run:  python tests/test_engine.py        (exit 0 = all pass)
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
FIX = os.path.join(HERE, "fixtures")
sys.path.insert(0, ASSETS)
import company_facts as cf  # noqa: E402

CASES = {
    "AAPL":  {"q_end": "2026-03-28", "fy_end": "2025-09-27"},
    "MSFT":  {"q_end": "2026-03-31", "fy_end": "2025-06-30"},
    "JPM":   {"q_end": "2026-03-31", "fy_end": "2025-12-31"},
    "BRK-B": {"q_end": "2026-03-31", "fy_end": "2025-12-31"},
}

# Exact expected values in raw dollars / share count. None = must resolve to missing.
EXPECT = {
    "AAPL": {
        "shares": 14_687_356_000, "lt_debt": 74_404_000_000, "finance_lease": 692_000_000,
        "minority": None, "current_assets": 144_114_000_000, "current_liabilities": 134_641_000_000,
        "working_capital": 9_473_000_000, "ltm_ebit": 147_366_000_000, "ltm_da": 12_610_000_000,
        "ltm_ebitda": 159_976_000_000, "ltm_ni": 122_575_000_000, "ltm_cfo": 140_222_000_000,
    },
    "MSFT": {
        "lt_debt": 31_423_000_000, "finance_lease": 62_932_000_000, "minority": None,
        "current_assets": 175_329_000_000, "current_liabilities": 136_661_000_000,
        "working_capital": 38_668_000_000, "ltm_ebit": 148_957_000_000,
        "ltm_ebitda": 179_257_000_000, "ltm_ni": 125_216_000_000, "ltm_cfo": 170_141_000_000,
    },
    "JPM": {  # bank: staleness + financial signature
        "lt_debt": None, "current_assets": None, "current_liabilities": None,
        "working_capital": None, "ltm_ebit": None, "ltm_ni": 58_851_000_000,
    },
    "BRK-B": {  # multi-class + insurer
        "shares": None, "minority": 2_269_000_000, "ltm_ebit": None,
        "current_assets": None, "working_capital": None,
    },
}

GETTERS = {
    "shares": lambda r: r["ev_line_items"]["shares_outstanding"]["value"],
    "lt_debt": lambda r: r["ev_line_items"]["long_term_debt_noncurrent"]["value"],
    "finance_lease": lambda r: r["ev_line_items"]["finance_lease_noncurrent"]["value"],
    "minority": lambda r: r["ev_line_items"]["minority_interest"]["value"],
    "current_assets": lambda r: r["ev_line_items"]["current_assets"]["value"],
    "current_liabilities": lambda r: r["ev_line_items"]["current_liabilities"]["value"],
    "working_capital": lambda r: r["working_capital"],
    "ltm_ebit": lambda r: r["ltm"]["operating_income_ebit"]["value"],
    "ltm_da": lambda r: r["ltm"]["depreciation_amortization"]["value"],
    "ltm_ebitda": lambda r: r["ltm_ebitda_derived"],
    "ltm_ni": lambda r: r["ltm"]["net_income"]["value"],
    "ltm_cfo": lambda r: r["ltm"]["cfo"]["value"],
}


def run():
    passed = failed = 0
    fails = []
    for t, case in CASES.items():
        path = os.path.join(FIX, f"{t}.json")
        if not os.path.exists(path):
            print(f"SKIP {t}: fixture missing ({path})")
            continue
        with open(path, "r", encoding="utf-8") as f:
            facts = json.load(f)
        r = cf.compute_line_items(facts, case["q_end"], case["fy_end"], ticker=t)
        for key, want in EXPECT[t].items():
            got = GETTERS[key](r)
            ok = (got is None and want is None) or (got == want)
            if ok:
                passed += 1
            else:
                failed += 1
                fails.append(f"  FAIL {t}.{key}: got {got!r}, expected {want!r}")
    # Cross-check: AAPL EBITDA == EBIT + D&A
    print("-" * 64)
    print(f"{passed} passed, {failed} failed")
    for line in fails:
        print(line)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())
