#!/usr/bin/env python3
"""
test_verify.py — Deterministic, offline test of the 10-Q balance-sheet reader (verify_filing.py),
which reads the PRIMARY filing to catch debt the XBRL API can't expose. Uses a synthetic balance
sheet (no network, no real ticker) so it exercises: balance-sheet selection from FilingSummary,
scale detection, total-liabilities pickup, and debt-like classification (include notes/secured/
related-party; EXCLUDE leases, payables, and equity-linked warrants/derivatives).
Run: python tests/test_verify.py
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
sys.path.insert(0, ASSETS)
import fetch_edgar as fe
import verify_filing as vf

FILING_SUMMARY = (
    "<FilingSummary><MyReports>"
    "<Report><ShortName>Condensed Consolidated Balance Sheets</ShortName>"
    "<LongName>Balance Sheets</LongName><HtmlFileName>R2.htm</HtmlFileName></Report>"
    "<Report><ShortName>Condensed Consolidated Balance Sheets (Parenthetical)</ShortName>"
    "<HtmlFileName>R3.htm</HtmlFileName></Report>"
    "</MyReports></FilingSummary>"
)
# A synthetic balance sheet ($ in thousands): assets, then liabilities (incl. a custom-tag-style
# related-party note + a warrant liability), then equity.
BALANCE_SHEET = """<html><body><p>($ in thousands)</p><table>
<tr><td>Cash and cash equivalents</td><td>205,194</td></tr>
<tr><td>Note receivable - related party</td><td>1,000</td></tr>
<tr><td>Total assets</td><td>646,600</td></tr>
<tr><td>Accounts payable</td><td>20,000</td></tr>
<tr><td>Operating lease liability, noncurrent</td><td>33,147</td></tr>
<tr><td>Revenue interest liability</td><td>404,299</td></tr>
<tr><td>Related-party convertible note payable, at fair value</td><td>678,386</td></tr>
<tr><td>Warrant liabilities</td><td>308,222</td></tr>
<tr><td>Total liabilities</td><td>1,515,763</td></tr>
<tr><td>Total stockholders' equity (deficit)</td><td>(870,006)</td></tr>
</table></body></html>"""


# Same balance sheet but with NO scale header -> extract_rows defaults scale to 1 (the 1000x risk).
NO_SCALE_BS = BALANCE_SHEET.replace("($ in thousands)", "(in dollars)")

BS = {"html": BALANCE_SHEET}  # switchable so tests can simulate a misdetected scale


def _fake_get(url, **kw):
    return (FILING_SUMMARY if url.endswith("FilingSummary.xml") else BS["html"]).encode("utf-8")


fe._get = _fake_get  # isolated: selfcheck runs each test file in its own subprocess


def run():
    fails, n = [], [0]

    def ck(name, cond):
        n[0] += 1
        if not cond:
            fails.append("  FAIL " + name)

    r = vf.verify_liabilities(1234, "0001234-26-000001")
    labels = [l for l, v in r["debt_like_rows"]]
    debt_total = sum(v for l, v in r["debt_like_rows"])

    ck("selected the balance sheet (not parenthetical)", r["url"].endswith("R2.htm"))
    ck("scale detected = thousands", r["scale"] == 1000)
    ck("total liabilities = 1,515,763k", abs(r["total_liabilities"] - 1_515_763_000) < 1)
    ck("revenue interest liability captured", any("Revenue interest" in l for l in labels))
    ck("related-party note captured (XBRL can't see it)", any("Related-party convertible" in l for l in labels))
    ck("warrants EXCLUDED (equity-linked)", not any("Warrant" in l for l in labels))
    ck("leases EXCLUDED", not any("lease" in l.lower() for l in labels))
    ck("payables EXCLUDED", not any("payable" in l.lower() and "note" not in l.lower() for l in labels))
    ck("asset-side note receivable EXCLUDED", not any("receivable" in l.lower() for l in labels))
    ck("debt-like total = 1,082,685k (404,299 + 678,386)", abs(debt_total - 1_082_685_000) < 1)
    ck("no scale_note when XBRL total not supplied", r.get("scale_note") is None)

    # --- scale cross-check: XBRL total matches the (correctly-scaled) statement -> no correction ---
    r = vf.verify_liabilities(1234, "x", xbrl_total_liabilities=1_515_763_000)
    ck("matching XBRL total -> no scale correction", r.get("scale_note") is None)
    ck("matching XBRL total -> total unchanged", abs(r["total_liabilities"] - 1_515_763_000) < 1)

    # --- scale cross-check: scale MISDETECTED as 1 (no header), reconciled to XBRL -> auto x1000 ---
    BS["html"] = NO_SCALE_BS
    try:
        r = vf.verify_liabilities(1234, "x", xbrl_total_liabilities=1_515_763_000)
        ck("misdetected scale auto-corrected (note present)",
           "auto-corrected" in (r.get("scale_note") or ""))
        ck("corrected total liabilities = 1,515,763,000", abs(r["total_liabilities"] - 1_515_763_000) < 1)
        ck("corrected debt-like total = 1,082,685,000",
           abs(sum(v for _, v in r["debt_like_rows"]) - 1_082_685_000) < 1)
        ck("effective scale now 1000", abs(r["scale"] - 1000) < 1e-9)
    finally:
        BS["html"] = BALANCE_SHEET

    # --- scale cross-check: totals that don't reconcile at all -> warning (no silent correction) ---
    r = vf.verify_liabilities(1234, "x", xbrl_total_liabilities=5_000_000_000)
    ck("non-reconciling totals -> WARNING", "WARNING" in (r.get("scale_note") or ""))

    print("-" * 60)
    print(f"{n[0] - len(fails)}/{n[0]} passed" + ("" if not fails else f", {len(fails)} FAILED"))
    for f in fails:
        print(f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(run())
