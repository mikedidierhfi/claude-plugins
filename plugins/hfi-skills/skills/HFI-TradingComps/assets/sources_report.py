#!/usr/bin/env python3
"""
sources_report.py — Build a markdown "Sources & citations" block from an assembled comps dict, with
clickable links to every primary source and (best-effort) DEEP links to the exact statement page
(balance sheet / income statement / cash flows). This block is meant to be returned in the chat reply
so the user can click straight through to each figure's source — not just read the workbook footnotes.

  build_sources_markdown(comps, cache_dir=None, with_statement_links=True) -> str

`with_statement_links=True` fetches each filing's FilingSummary to resolve the exact statement R-file
URLs (network, best-effort per filing — degrades to the filing-index link if it can't). Set False for
a fast/offline block (filing-index links + per-figure XBRL citations only).
"""
import verify_filing as vf

EDGAR_BROWSE = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}"
                "&type=10-K&dateb=&owner=include&count=40")

LINE_ITEMS = [
    ("shares_outstanding", "Shares outstanding"),
    ("long_term_debt_noncurrent", "Long-term debt"),
    ("finance_lease_noncurrent", "Finance/capital leases"),
    ("minority_interest", "Minority interest"),
    ("redeemable_minority_interest", "Redeemable (mezzanine) NCI"),
    ("preferred_equity", "Preferred equity"),
    ("current_assets", "Total current assets"),
    ("current_liabilities", "Total current liabilities"),
    ("cash_and_equivalents", "Cash & equivalents"),
]
LTM_ITEMS = [("revenue", "Revenue"), ("operating_income_ebit", "EBIT"),
             ("depreciation_amortization", "D&A"), ("net_income", "Net income"), ("cfo", "CFO")]


def _cite_str(c):
    if not isinstance(c, dict):
        return None
    return f"`{c.get('tag')}` — {c.get('form')} period ended {c.get('end')} (accession {c.get('accn')})"


def build_sources_markdown(comps, cache_dir=None, with_statement_links=True):
    out = ["## Sources & citations",
           "*Every figure traces to a primary SEC filing or the live price feed; links open the exact "
           "document/statement.*"]
    for t in comps.get("tickers", []):
        co = comps["companies"].get(t, {})
        cik = co.get("cik")
        out.append("")
        out.append(f"### {t} — {co.get('title', '')}")
        if cik:
            out.append(f"CIK {cik} · [all SEC filings]({EDGAR_BROWSE.format(cik=cik)})")

        if co.get("price") is not None:
            seg = f"- **Price:** ${co['price']} as of {co.get('price_as_of', '')} — {co.get('price_source', '')}"
            if co.get("price_source_url"):
                seg += f" ([source]({co['price_source_url']}))"
            out.append(seg)

        for key, lbl in (("filing_10q", "10-Q"), ("filing_10k", "10-K")):
            f = co.get(key) or {}
            if not f:
                continue
            seg = (f"- **{lbl}** — period {f.get('reportDate')}, filed {f.get('filingDate')}, "
                   f"accession {f.get('accession')}")
            if f.get("url"):
                seg += f": [filing index]({f['url']})"
            if with_statement_links and cik and f.get("accession"):
                try:
                    st = vf.find_statements(cik, f["accession"])
                    pages = [f"[{p}]({st[k]})" for k, p in
                             (("balance_sheet", "balance sheet"), ("income", "income statement"),
                              ("cash_flow", "cash flows")) if st.get(k)]
                    if pages:
                        seg += " · exact pages: " + " · ".join(pages)
                except Exception:
                    pass
            out.append(seg)

        cites = co.get("citations") or {}
        detail = []
        for k, lbl in LINE_ITEMS:
            s = _cite_str(cites.get(k))
            if s:
                detail.append(f"  - {lbl}: {s}")
        ltmc = co.get("ltm_components") or {}
        for k, lbl in LTM_ITEMS:
            comp = ltmc.get(k)
            if not isinstance(comp, dict):
                continue
            parts = []
            for ck, clabel in (("fy", "FY"), ("ytd", "YTD"), ("prior_ytd", "prior-YTD")):
                cc = comp.get(ck)
                if isinstance(cc, dict):
                    parts.append(f"{clabel} {cc.get('form')} {cc.get('start')}->{cc.get('end')}")
            if parts:
                detail.append(f"  - {lbl} (LTM bridge): " + "; ".join(parts))
        if detail:
            out.append("- **Line-item citations** (XBRL concept · form · period · accession):")
            out.extend(detail)
    return "\n".join(out)


if __name__ == "__main__":
    import json, sys
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        comps = json.load(fh)
    print(build_sources_markdown(comps, with_statement_links=("--no-net" not in sys.argv)))
