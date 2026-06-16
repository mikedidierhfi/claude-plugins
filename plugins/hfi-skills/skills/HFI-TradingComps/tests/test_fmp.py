#!/usr/bin/env python3
"""
test_fmp.py — Offline test for fmp_consensus (NTM via Financial Modeling Prep). Injects a synthetic
annual-estimates list (no network, no key) and verifies the calendarized NTM blend math, the $mm
conversion, the CFO-stays-blank rule, past-year filtering, and the key-resolution order.
Run: python tests/test_fmp.py
"""
import datetime as dt
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import fmp_consensus as fc  # noqa: E402

# synthetic annual consensus ($ raw): one past FY (must be filtered) + FY1 + FY2
EST = [
    {"date": "2025-09-27", "ebitdaAvg": 90e9, "ebitAvg": 80e9, "netIncomeAvg": 70e9, "revenueAvg": 380e9},
    {"date": "2026-09-27", "ebitdaAvg": 100e9, "ebitAvg": 88e9, "netIncomeAvg": 78e9, "revenueAvg": 400e9},
    {"date": "2027-09-26", "ebitdaAvg": 120e9, "ebitAvg": 104e9, "netIncomeAvg": 92e9, "revenueAvg": 440e9},
]
AS_OF = "2026-06-15"
F = (dt.date(2026, 9, 27) - dt.date(2026, 6, 15)).days / 365.0  # weight on FY1


def run():
    fails, n = [], [0]

    def ck(name, cond):
        n[0] += 1
        if not cond:
            fails.append("  FAIL " + name)

    def near(a, b, tol=1e-3):
        return a is not None and abs(a - b) <= tol

    rec = fc.ntm_for("AAPL", "k", as_of=AS_OF, _fetch=lambda: EST)
    ck("record returned", rec is not None)
    ck("CFO stays blank (FMP has no CFO estimate)", rec["ntm_cfo"] is None)
    # calendarized blend, in $mm
    ck("NTM EBITDA = blend(FY1,FY2)/1e6", near(rec["ntm_ebitda"], (F * 100e9 + (1 - F) * 120e9) / 1e6))
    ck("NTM EBIT  = blend(FY1,FY2)/1e6", near(rec["ntm_ebit"], (F * 88e9 + (1 - F) * 104e9) / 1e6))
    ck("NTM NI    = blend(FY1,FY2)/1e6", near(rec["ntm_net_income"], (F * 78e9 + (1 - F) * 92e9) / 1e6))
    ck("NTM revenue present", rec["ntm_revenue"] is not None)
    ck("blend lands between FY1 and FY2 (mm)", 100000.0 < rec["ntm_ebitda"] < 120000.0)
    ck("weighted toward FY2 (1-F > F)", rec["ntm_ebitda"] > (100000.0 + 120000.0) / 2)
    ck("source names both fiscal years", "FY2026" in rec["source"] and "FY2027" in rec["source"])

    # only one future FY -> use it directly (no blend, no crash)
    one = fc.ntm_for("X", "k", as_of=AS_OF, _fetch=lambda: [EST[1]])
    ck("single-FY uses FY1 directly", near(one["ntm_ebitda"], 100e9 / 1e6))

    # empty / no future estimates -> None
    ck("empty estimates -> None", fc.ntm_for("X", "k", as_of=AS_OF, _fetch=lambda: []) is None)
    ck("all-past estimates -> None", fc.ntm_for("X", "k", as_of="2030-01-01", _fetch=lambda: EST) is None)

    # fetch_ntm wraps per-ticker and never raises (monkeypatch ntm_for so no network is touched)
    saved_ntm = fc.ntm_for

    def stub(sym, key, as_of=None):
        if sym == "BOOM":
            raise RuntimeError("network down")
        return {"ntm_ebitda": 1.0} if sym == "AAPL" else None
    fc.ntm_for = stub
    try:
        data, notes = fc.fetch_ntm(["AAPL", "MISS", "BOOM"], "k", as_of=AS_OF)
        ck("fetch_ntm keyed by ticker", set(data.keys()) == {"AAPL", "MISS", "BOOM"})
        ck("fetch_ntm maps a hit", data["AAPL"] == {"ntm_ebitda": 1.0})
        ck("fetch_ntm tolerates a miss", data["MISS"] is None)
        ck("fetch_ntm swallows a per-ticker error", data["BOOM"] is None)
        ck("notes explain a miss", bool(notes.get("MISS")))
        ck("notes explain an error", "RuntimeError" in notes.get("BOOM", ""))
        ck("no note for a hit", "AAPL" not in notes)
    finally:
        fc.ntm_for = saved_ntm

    # HTTP 402 (symbol not on the FMP plan) -> blank + an explicit plan note (the AVGO/QCOM case)
    import urllib.error
    saved_ntm2 = fc.ntm_for

    def stub402(sym, key, as_of=None):
        raise urllib.error.HTTPError("u", 402, "Payment Required", {}, None)
    fc.ntm_for = stub402
    try:
        data, notes = fc.fetch_ntm(["AVGO"], "k", as_of=AS_OF)
        ck("402 -> blank NTM", data["AVGO"] is None)
        ck("402 -> note cites plan + 402", "402" in notes["AVGO"] and "plan" in notes["AVGO"])
    finally:
        fc.ntm_for = saved_ntm2

    # key resolution: env var wins
    old = os.environ.get("FMP_API_KEY")
    os.environ["FMP_API_KEY"] = "ENVKEY123"
    try:
        ck("get_key reads FMP_API_KEY", fc.get_key() == "ENVKEY123")
    finally:
        if old is None:
            os.environ.pop("FMP_API_KEY", None)
        else:
            os.environ["FMP_API_KEY"] = old

    # key resolution: config file (env unset), via a temp config path
    saved_env = os.environ.pop("FMP_API_KEY", None)
    saved_path = fc.CONFIG_PATH
    try:
        tmp = os.path.join(tempfile.gettempdir(), "hfi_tc_test_key.json")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write('{"fmp_api_key": "FILEKEY456"}')
        fc.CONFIG_PATH = tmp
        ck("get_key falls back to config file", fc.get_key() == "FILEKEY456")
        os.remove(tmp)
    finally:
        fc.CONFIG_PATH = saved_path
        if saved_env is not None:
            os.environ["FMP_API_KEY"] = saved_env

    print("-" * 56)
    print(f"{n[0] - len(fails)}/{n[0]} passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
