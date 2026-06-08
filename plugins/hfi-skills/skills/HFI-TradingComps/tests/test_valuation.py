#!/usr/bin/env python3
"""
test_valuation.py — Deterministic regression test for the ORCHESTRATOR math (build_comps.assemble):
the TEV bridge, valuation multiples, nm/blank handling, $mm scaling, the --shares override, and
is_financial detection. The Excel workbook re-expresses exactly this math as live formulas, so
locking it here is the core "same results every time" guarantee.

No network: cf.build_line_items and mp.get_price are monkeypatched to return fixed synthetic data.
Run: python tests/test_valuation.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import build_comps as bc
import company_facts as cf
import market_price as mp


def li(ticker, shares=1_000_000_000, lt_debt=10_000_000_000, lease=1_000_000_000,
       minority=500_000_000, ca=8_000_000_000, cl=5_000_000_000, cash=2_000_000_000,
       rev=20_000_000_000, ebit=4_000_000_000, da=1_000_000_000, ni=2_000_000_000,
       cfo=3_000_000_000):
    def inst(v):
        return {"value": v, "citation": "test"}
    wc = (ca - cl) if (ca is not None and cl is not None) else None
    ebitda = (ebit + da) if (ebit is not None and da is not None) else None
    return {
        "ticker": ticker, "title": f"{ticker} Test Co", "cik": 1, "fiscalYearEnd": "1231",
        "latest_10Q": {"reportDate": "2026-03-31", "accession": "x", "url": "u"},
        "latest_10K": {"reportDate": "2025-12-31", "accession": "y", "url": "u"},
        "ev_line_items": {
            "shares_outstanding": inst(shares), "long_term_debt_noncurrent": inst(lt_debt),
            "finance_lease_noncurrent": inst(lease), "minority_interest": inst(minority),
            "current_assets": inst(ca), "current_liabilities": inst(cl),
            "cash_and_equivalents": inst(cash),
        },
        "working_capital": wc,
        "ltm": {"revenue": inst(rev), "operating_income_ebit": inst(ebit),
                "depreciation_amortization": inst(da), "net_income": inst(ni), "cfo": inst(cfo)},
        "ltm_ebitda_derived": ebitda,
    }

# Per-ticker synthetic fixtures
FIX = {
    "OPER": li("OPER"),                                              # clean operating co
    "LOSS": li("LOSS", ebit=-1_000_000_000, da=200_000_000, ni=-500_000_000),  # loss-maker
    "FIN":  li("FIN", ca=None, cl=None, ebit=None, da=None, minority=None, lt_debt=None),  # financial
}
PRICE = {"OPER": 50.0, "LOSS": 50.0, "FIN": 50.0}

def _resolve(t, cache=None):
    if t.upper() == "BADTKR":
        raise KeyError(t)        # simulate an unresolvable ticker
    return {"cik": 1, "title": f"{t} Test Co"}


cf.build_line_items = lambda t, cache: FIX[t]
cf.fe.resolve_cik = _resolve
mp.get_price = lambda t: {"price": PRICE[t], "as_of": "2026-06-05", "source": "test", "source_url": "u"}


def approx(a, b, tol=1e-6):
    return a is not None and b is not None and abs(a - b) <= tol


def run():
    fails = []
    n = [0]

    def ck(name, cond):
        n[0] += 1
        if not cond:
            fails.append("  FAIL " + name)

    # --- Clean operating company: exact TEV + multiples ---
    c = bc.assemble(["OPER"], "")["companies"]["OPER"]
    ck("OPER market_equity 50000", approx(c["market_equity_mm"], 50000.0))
    ck("OPER working_capital 3000", approx(c["working_capital_mm"], 3000.0))
    ck("OPER TEV 58500 (=50000+10000+1000+500-3000)", approx(c["tev_mm"], 58500.0))
    ck("OPER EBITDA 5000", approx(c["ltm_mm"]["ebitda"], 5000.0))
    ck("OPER TEV/EBITDA 11.7", approx(c["multiples"]["ev_ebitda_ltm"], 11.7))
    ck("OPER TEV/EBIT 14.625", approx(c["multiples"]["ev_ebit_ltm"], 14.625))
    ck("OPER TEV/CFO 19.5", approx(c["multiples"]["ev_cfo_ltm"], 19.5))
    ck("OPER TEV/NI 29.25", approx(c["multiples"]["ev_ni_ltm"], 29.25))
    ck("OPER P/E 25.0", approx(c["pe_ltm"], 25.0))
    ck("OPER not financial", c["is_financial"] is False)

    # --- Loss-maker: non-positive denominators -> 'nm' (never a negative multiple) ---
    c = bc.assemble(["LOSS"], "")["companies"]["LOSS"]
    ck("LOSS TEV/EBIT nm", c["multiples"]["ev_ebit_ltm"] == "nm")
    ck("LOSS TEV/EBITDA nm", c["multiples"]["ev_ebitda_ltm"] == "nm")
    ck("LOSS TEV/NI nm", c["multiples"]["ev_ni_ltm"] == "nm")

    # --- Financial (no classified BS, no EBIT) -> flagged, WC omitted, EV multiples blank ---
    c = bc.assemble(["FIN"], "")["companies"]["FIN"]
    ck("FIN is_financial", c["is_financial"] is True)
    ck("FIN working_capital None", c["working_capital_mm"] is None)
    ck("FIN TEV/EBITDA None", c["multiples"]["ev_ebitda_ltm"] is None)

    # --- --shares override ---
    c = bc.assemble(["OPER"], "", shares_override={"OPER": 2_000_000_000})["companies"]["OPER"]
    ck("override shares 2000mm", approx(c["shares_mm"], 2000.0))
    ck("override market_equity 100000", approx(c["market_equity_mm"], 100000.0))
    ck("override flagged", any("supplied value" in f for f in c["flags"]))

    # --- graceful degradation: a bad ticker is dropped (flagged), the rest still build ---
    comps = bc.assemble(["OPER", "BADTKR"], "")
    ck("bad ticker dropped from tickers", comps["tickers"] == ["OPER"])
    ck("good ticker still built", "OPER" in comps["companies"])
    ck("bad ticker recorded in errors", any(e["ticker"] == "BADTKR" for e in comps["errors"]))

    print("-" * 60)
    print(f"{n[0] - len(fails)}/{n[0]} passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
