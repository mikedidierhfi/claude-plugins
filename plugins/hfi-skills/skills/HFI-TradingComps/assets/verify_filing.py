#!/usr/bin/env python3
"""
verify_filing.py — Read the ACTUAL balance sheet from a 10-Q/10-K and reconcile it against the XBRL
pull. General for any filer: EDGAR renders every filing's statements as R*.htm files indexed by
FilingSummary.xml. We locate the balance-sheet report by title, extract its rows (label + current-
period value), and surface the liability/debt lines — so debt that companyfacts can't expose (custom
or related-party tags) is still caught by reading the primary document.

This is the verification step behind the liabilities-completeness flag: when the XBRL capture looks
incomplete, read the statement and show the analyst the real liability lines (and a debt-candidate
total) to confirm or correct long-term debt (via build_comps --debt).

CLI:
  python verify_filing.py IBRX            # latest 10-Q balance-sheet liabilities
  python verify_filing.py AAPL --filing 10-K
"""
import argparse, re, sys
import fetch_edgar as fe

DEBT_RE = re.compile(r"(note|debt|borrow|loan|convertible|revenue interest|secured|promissory|"
                     r"credit facilit|term loan|senior|subordinat|related part|financing)", re.I)
# liabilities that are NOT house "debt" (leases excluded separately; these shouldn't count as debt)
NONDEBT_RE = re.compile(r"(deferred revenue|deferred income tax|operating lease|accounts payable|"
                        r"accrued|warrant|derivative|deferred rent|pension|income tax payable|"
                        r"contract liabilit|other liabilit)", re.I)


def _reports(cik, accession):
    accn = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn}"
    xml = fe._get(f"{base}/FilingSummary.xml").decode("utf-8", "replace")
    out = []
    for m in re.finditer(r"<Report\b.*?</Report>", xml, re.S):
        blk = m.group(0)
        name = " ".join(re.findall(r"<(?:ShortName|LongName)>(.*?)</(?:ShortName|LongName)>", blk, re.S))
        f = re.search(r"<HtmlFileName>(.*?)</HtmlFileName>", blk, re.S)
        if f:
            out.append((name.lower(), f.group(1).strip()))
    return base, out


def find_balance_sheet(cik, accession):
    base, reports = _reports(cik, accession)
    for name, fn in reports:
        if ("balance sheet" in name or "financial position" in name) and "parenthetical" not in name:
            return f"{base}/{fn}"
    return None


def extract_rows(url):
    """Return [(label, value_in_dollars)] for each balance-sheet row, plus the detected scale."""
    html = fe._get(url).decode("utf-8", "replace")
    head = re.sub(r"<[^>]+>", " ", html[:6000]).lower()
    scale = 1000 if "in thousands" in head else (1_000_000 if "in millions" in head else 1)
    rows = []
    for trm in re.finditer(r"<tr\b.*?</tr>", html, re.S):
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).replace(" ", " ").strip()
                 for c in re.findall(r"<t[dh]\b.*?</t[dh]>", trm.group(0), re.S)]
        label = next((c for c in cells if re.search(r"[A-Za-z]", c)), "")
        val = None
        for c in cells:
            tt = c.replace(",", "").replace("$", "").strip()
            if re.fullmatch(r"\(?-?\d+(\.\d+)?\)?", tt):
                num = float(tt.strip("()").lstrip("-"))
                val = -num if (tt.startswith("(") or tt.startswith("-")) else num
                val *= scale
                break
        if label and val is not None:
            rows.append((label, val))
    return rows, scale


def verify_liabilities(cik, accession):
    url = find_balance_sheet(cik, accession)
    if not url:
        return {"url": None, "error": "balance-sheet statement not found in FilingSummary"}
    rows, scale = extract_rows(url)
    # Restrict to the liabilities section (after the asset section ends at "Total assets") so
    # asset-side items like notes/loans receivable or "due from related parties" aren't mistaken for debt.
    start = 0
    for i, (l, v) in enumerate(rows):
        if re.fullmatch(r"total assets", l.strip(), re.I):
            start = i + 1
            break
    liab_rows = rows[start:]
    total_liab = next((v for (l, v) in liab_rows if re.fullmatch(r"total liabilities", l.strip(), re.I)), None)
    debt_rows = [(l, v) for (l, v) in liab_rows if DEBT_RE.search(l) and not NONDEBT_RE.search(l)]
    return {"url": url, "scale": scale, "total_liabilities": total_liab,
            "debt_like_rows": debt_rows, "all_rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--out", default=fe.DEFAULT_CACHE)
    ap.add_argument("--filing", default="10-Q", choices=["10-Q", "10-K"])
    ap.add_argument("--all", action="store_true", help="print every balance-sheet row")
    args = ap.parse_args(argv)
    meta = fe.fetch_ticker(args.ticker, args.out)
    f = meta.get("latest_10Q" if args.filing == "10-Q" else "latest_10K") or {}
    r = verify_liabilities(meta["cik"], f.get("accession"))
    print(f"{args.ticker.upper()} {args.filing} {f.get('accession')}")
    print(f"balance sheet: {r.get('url')}")
    if r.get("error"):
        print("ERROR:", r["error"]); return 1
    if r.get("total_liabilities") is not None:
        print(f"Total liabilities (per statement): ${r['total_liabilities']/1e6:,.1f}mm")
    print("DEBT-LIKE liability lines (verify vs the XBRL long-term-debt capture):")
    for l, v in r["debt_like_rows"]:
        print(f"  {l[:62]:62} ${v/1e6:,.1f}mm")
    if args.all:
        print("\nALL rows:")
        for l, v in r["all_rows"]:
            print(f"  {l[:62]:62} ${v/1e6:,.1f}mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
