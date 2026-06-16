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
       cfo=3_000_000_000, total_liab=None, op_lease=0, def_tax=0, other_liab=0, equity=None,
       redeem_nci=None, preferred=None, nc_inv=None, share_classes=1,
       ebit_method="FY + YTD - priorYTD", da_method="FY + YTD - priorYTD"):
    def inst(v):
        return {"value": v, "citation": "test"}

    def flow(v, method):
        return {"value": v, "citation": "test", "method": method}
    wc = (ca - cl) if (ca is not None and cl is not None) else None
    ebitda = (ebit + da) if (ebit is not None and da is not None) else None
    return {
        "ticker": ticker, "title": f"{ticker} Test Co", "cik": 1, "fiscalYearEnd": "1231",
        "latest_10Q": {"reportDate": "2026-03-31", "accession": "x", "url": "u"},
        "latest_10K": {"reportDate": "2025-12-31", "accession": "y", "url": "u"},
        "ev_line_items": {
            "shares_outstanding": inst(shares), "long_term_debt_noncurrent": inst(lt_debt),
            "finance_lease_noncurrent": inst(lease), "minority_interest": inst(minority),
            "redeemable_minority_interest": inst(redeem_nci),
            "preferred_equity": inst(preferred), "noncurrent_investments": inst(nc_inv),
            "current_assets": inst(ca), "current_liabilities": inst(cl),
            "cash_and_equivalents": inst(cash),
            "total_liabilities": inst(total_liab), "liabilities_noncurrent": inst(None),
            "operating_lease_noncurrent": inst(op_lease), "deferred_tax_noncurrent": inst(def_tax),
            "other_liabilities_noncurrent": inst(other_liab), "stockholders_equity": inst(equity),
        },
        "working_capital": wc,
        "ltm": {"revenue": flow(rev, ebit_method), "operating_income_ebit": flow(ebit, ebit_method),
                "depreciation_amortization": flow(da, da_method), "net_income": flow(ni, ebit_method),
                "cfo": flow(cfo, ebit_method)},
        "ltm_ebitda_derived": ebitda,
        "share_classes_detected": share_classes,
    }

# Per-ticker synthetic fixtures
FIX = {
    "OPER": li("OPER"),                                              # clean operating co
    "LOSS": li("LOSS", ebit=-1_000_000_000, da=200_000_000, ni=-500_000_000),  # loss-maker
    "FIN":  li("FIN", ca=None, cl=None, ebit=None, da=None, minority=None, lt_debt=None),  # financial
    # IBRX-like: standard tags capture $0 debt, but total liabilities reveal ~$4.9bn of non-current
    # liabilities (debt under a custom/related-party tag) -> reconciliation flag must fire.
    "HIDDENDEBT": li("HIDDENDEBT", lt_debt=0, lease=0, minority=0, ca=1_000_000_000,
                     cl=100_000_000, total_liab=5_000_000_000, equity=-1_000_000_000),
    # preferred + redeemable (mezzanine) NCI both present -> summed into the bridge
    "PREF": li("PREF", minority=500_000_000, redeem_nci=300_000_000, preferred=400_000_000),
    # D&A degraded to FY-only while EBIT is true LTM -> EBITDA basis-mismatch flag
    "MISMATCH": li("MISMATCH", da_method="FY only (YTD/prior incomplete)"),
    # multiple share classes detected -> understated-shares flag
    "MULTI": li("MULTI", share_classes=2),
    # large non-operating long-term investment portfolio -> materiality flag (NOT netted)
    "BIGINV": li("BIGINV", nc_inv=30_000_000_000),
}
PRICE = {"OPER": 50.0, "LOSS": 50.0, "FIN": 50.0, "HIDDENDEBT": 50.0}

def _resolve(t, cache=None):
    if t.upper() == "BADTKR":
        raise KeyError(t)        # simulate an unresolvable ticker
    return {"cik": 1, "title": f"{t} Test Co"}


cf.build_line_items = lambda t, cache: FIX[t]
cf.fe.resolve_cik = _resolve
mp.get_price = lambda t: {"price": PRICE.get(t, 50.0), "as_of": "2026-06-05", "source": "test", "source_url": "u"}
# Stub the 10-Q balance-sheet reader (offline + deterministic) so the reconciliation flag's
# primary-source verification step is exercised without network.
bc.vf.verify_liabilities = lambda cik, acc, xbrl_total_liabilities=None: {
    "debt_like_rows": [("Related-party convertible note payable", 4_800_000_000.0)],
    "total_liabilities": 5_000_000_000.0, "url": "u", "scale": 1000, "scale_note": None}


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

    # --- liabilities-completeness: uncaptured non-current liabilities (custom-tag debt) -> flag ---
    c = bc.assemble(["HIDDENDEBT"], "")["companies"]["HIDDENDEBT"]
    ck("reconciliation flag fires on hidden debt", any("NOT captured by" in f for f in c["flags"]))
    ck("flag reads the 10-Q + suggests --debt",
       any(("Reading the 10-Q" in f and "--debt" in f) for f in c["flags"]))
    ck("negative book equity flagged", any("Negative book equity" in f for f in c["flags"]))

    # --- --debt override: injects verified debt, suppresses the reconciliation nag, lifts TEV ---
    c = bc.assemble(["HIDDENDEBT"], "", debt_override={"HIDDENDEBT": 1_000_000_000})["companies"]["HIDDENDEBT"]
    ck("debt override flagged", any("set to supplied value" in f for f in c["flags"]))
    ck("debt override suppresses reconciliation", not any("NOT captured by" in f for f in c["flags"]))
    ck("debt override flows into TEV (50,100mm)", approx(c["tev_mm"], 50100.0))

    # --- preferred + redeemable (mezzanine) NCI summed into the EV bridge ---
    c = bc.assemble(["PREF"], "")["companies"]["PREF"]
    ck("PREF minority summed (500+300=800)", approx(c["minority_mm"], 800.0))
    ck("PREF preferred captured (400)", approx(c["preferred_mm"], 400.0))
    ck("PREF TEV incl pref+redeem (59,200)", approx(c["tev_mm"], 59200.0))  # 50000+10000+1000+800+400-3000
    ck("PREF redeemable-NCI flag", any("Redeemable (mezzanine) NCI" in f for f in c["flags"]))
    ck("PREF preferred flag", any("Preferred equity" in f for f in c["flags"]))

    # --- a clean company must NOT spuriously gain the new flags ---
    c = bc.assemble(["OPER"], "")["companies"]["OPER"]
    ck("OPER no preferred flag", not any("Preferred equity" in f for f in c["flags"]))
    ck("OPER no redeemable-NCI flag", not any("Redeemable (mezzanine)" in f for f in c["flags"]))
    ck("OPER no mismatch flag", not any("basis mismatch" in f for f in c["flags"]))
    ck("OPER no multi-class flag", not any("Multiple share classes" in f for f in c["flags"]))
    ck("OPER preferred_mm None", c.get("preferred_mm") is None)

    # --- EBITDA period-basis mismatch (EBIT true-LTM, D&A FY-only) is flagged ---
    c = bc.assemble(["MISMATCH"], "")["companies"]["MISMATCH"]
    ck("EBITDA basis mismatch flagged", any("basis mismatch" in f for f in c["flags"]))

    # --- multiple share classes detected -> understated-shares flag ---
    c = bc.assemble(["MULTI"], "")["companies"]["MULTI"]
    ck("multi-class flag fires", any("Multiple share classes detected" in f for f in c["flags"]))
    c = bc.assemble(["MULTI"], "", shares_override={"MULTI": 2_000_000_000})["companies"]["MULTI"]
    ck("multi-class flag suppressed when --shares supplied",
       not any("Multiple share classes detected" in f for f in c["flags"]))

    # --- material long-term investments flagged but NOT netted from EV ---
    c = bc.assemble(["BIGINV"], "")["companies"]["BIGINV"]
    ck("LT-investments materiality flag", any("Long-term investments" in f for f in c["flags"]))
    ck("LT-investments NOT netted (TEV unchanged 58,500)", approx(c["tev_mm"], 58500.0))

    # --- NTM multiples must divide TEV($mm) by consensus($mm); guards the 1e6 unit bug ---
    saved_lc = bc.ci.load_consensus
    bc.ci.load_consensus = lambda tickers, path=None, fmp_key=None: {
        "consensus": {"OPER": {"ntm_ebitda": 5850.0, "ntm_ebit": 4500.0, "ntm_cfo": None,
                               "ntm_net_income": 2925.0, "source": "test", "as_of": "x",
                               "_provided": True}},
        "needs_consensus_for": [], "source_file": "test"}
    try:
        c = bc.assemble(["OPER"], "", consensus_mode="manual")["companies"]["OPER"]
        ck("NTM TEV/EBITDA = 10.0x (58,500/5,850, not 1e6 off)", approx(c["multiples"]["ev_ebitda_ntm"], 10.0))
        ck("NTM TEV/EBIT = 13.0x", approx(c["multiples"]["ev_ebit_ntm"], 13.0))
        ck("NTM TEV/NI = 20.0x", approx(c["multiples"]["ev_ni_ntm"], 20.0))
        ck("NTM TEV/CFO blank when consensus missing", c["multiples"]["ev_cfo_ntm"] is None)
    finally:
        bc.ci.load_consensus = saved_lc

    print("-" * 60)
    print(f"{n[0] - len(fails)}/{n[0]} passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
