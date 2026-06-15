#!/usr/bin/env python3
"""
build_comps.py — Orchestrator. Assembles the full trading-comps dataset for a set of tickers
and computes Total Enterprise Value (house definition) + valuation multiples. All display values
are in $ MILLIONS (shares in millions, price in $/share, multiples in x).

Pipeline:  fetch_edgar -> company_facts (line items + LTM) + market_price (price) +
           consensus_input (NTM)  ->  TEV bridge + multiples  ->  structured `comps` dict.

The Excel writer (build_comps_xlsx.py) renders this dict. Tests assert against it.

Usage:
  python build_comps.py AAPL MSFT
  python build_comps.py AAPL MSFT --xlsx out.xlsx --consensus consensus.json
"""
import argparse, datetime as dt, json, os, sys

import company_facts as cf
import market_price as mp
import consensus_input as ci
import verify_filing as vf

MM = 1_000_000.0


def _mm(x):
    return (x / MM) if x is not None else None


def _safe_mult(num, den):
    """TEV/metric. 'nm' (not meaningful) if denominator is missing or <= 0."""
    if num is None or den is None:
        return None
    if den <= 0:
        return "nm"
    return num / den


def assemble(tickers, cache_dir, consensus_path=None, as_of=None, include_pe=True,
             consensus_mode="skip", shares_override=None, prices_override=None,
             debt_override=None):
    as_of = as_of or dt.date.today().isoformat()
    shares_override = {k.upper(): v for k, v in (shares_override or {}).items()}
    prices_override = {k.upper(): v for k, v in (prices_override or {}).items()}
    debt_override = {k.upper(): v for k, v in (debt_override or {}).items()}
    cons = ci.load_consensus([t.upper() for t in tickers], consensus_path)

    companies = {}
    errors = []
    valid = []
    for t in tickers:  # pre-flight: drop unresolvable tickers so one typo can't kill the batch
        try:
            cf.fe.resolve_cik(t, cache_dir)
            valid.append(t)
        except KeyError:
            errors.append({"ticker": t.upper(), "error": "ticker not found on SEC EDGAR (typo? foreign filer? recently changed symbol?)"})
    for t in valid:
        T = t.upper()
        li = cf.build_line_items(T, cache_dir)
        if T in prices_override:
            price = {"price": prices_override[T], "as_of": as_of,
                     "source": "supplied price (offline / pinned)", "source_url": None}
        else:
            price = mp.get_price(T)
        ev = li["ev_line_items"]

        def item(k):
            return ev.get(k) or {}

        def val(k):
            return item(k).get("value")

        def stale_note(k, label):
            so = item(k).get("stale_only")
            if so:
                flags.append(f"{label}: only a stale value was available and was IGNORED ({so}) — "
                             f"supply a current figure from the latest filing if needed.")

        flags = []
        shares = val("shares_outstanding")
        if T in shares_override:
            shares = shares_override[T]
            flags.append(f"Shares outstanding set to supplied value {shares:,.0f} (e.g. Class A "
                         f"from the 10-Q cover) — overrides the XBRL default. For Up-C/multi-class "
                         f"issuers, total economic value also includes operating-group units (NCI).")
        p = price.get("price")
        market_equity = (shares * p) if (shares is not None and p is not None) else None
        if p is None:
            flags.append(f"Stock price unavailable ({price.get('error','')}). "
                         f"Provide via Chrome/manual; market cap & all multiples are blank until then.")
        if shares is None:
            flags.append("Shares outstanding not found in a recent filing — likely a multi-class "
                         "issuer (e.g. BRK, GOOG/GOOGL) or unusual XBRL tagging. Supply the current "
                         "share count(s) from the latest 10-Q cover page or a market source (sum all "
                         "classes x their prices). Market cap & all multiples are blank until provided.")
            stale_note("shares_outstanding", "Shares outstanding")

        lt_debt = val("long_term_debt_noncurrent")
        if T in debt_override:
            lt_debt = debt_override[T]
            flags.append(f"Long-term debt set to supplied value ${lt_debt/1e6:,.0f}mm (verified from the "
                         f"10-Q) — overrides the XBRL pull. Use this when debt is under custom/related-party "
                         f"tags the companyfacts API can't see.")
        elif lt_debt is None:
            flags.append("Long-term debt not found via standard XBRL tags — verify against the 10-Q.")
            stale_note("long_term_debt_noncurrent", "Long-term debt")
        fin_lease = val("finance_lease_noncurrent")
        if fin_lease is None:
            flags.append("Finance/capital lease obligations not separately reported — treated as $0.")
        minority = val("minority_interest")
        if minority is None:
            flags.append("No minority/noncontrolling interest reported — treated as $0.")
        ca = val("current_assets")
        cl = val("current_liabilities")
        wc = li.get("working_capital")
        if wc is None:
            flags.append("No classified balance sheet (current assets/liabilities not reported, "
                         "e.g. a bank/insurer) — working-capital adjustment omitted.")

        ltd = lt_debt or 0.0
        fl = fin_lease or 0.0
        mi = minority or 0.0
        wcu = wc or 0.0
        tev = (market_equity + ltd + fl + mi - wcu) if market_equity is not None else None

        # Liabilities-completeness reconciliation: flag material non-current liabilities NOT captured as
        # debt/leases/deferred-tax/other — i.e. debt under a custom or related-party XBRL tag the
        # companyfacts API doesn't expose (the IBRX case). Gated on materiality vs market cap so clean
        # large-caps with big (properly-tagged) "other" non-current liabilities don't false-positive.
        total_liab = val("total_liabilities")
        liab_nc = val("liabilities_noncurrent")
        nc_liab = liab_nc if liab_nc is not None else (
            (total_liab - cl) if (total_liab is not None and cl is not None) else None)
        if nc_liab is not None and T not in debt_override:
            captured_nc = ltd + fl + (val("operating_lease_noncurrent") or 0.0) \
                + (val("deferred_tax_noncurrent") or 0.0) + (val("other_liabilities_noncurrent") or 0.0)
            residual = nc_liab - captured_nc
            ref = market_equity if market_equity else (total_liab or nc_liab)
            if residual > max(50_000_000.0, 0.05 * ref):
                msg = (f"~${residual/1e6:,.0f}mm of non-current liabilities are NOT captured by standard "
                       f"debt/lease tags — likely debt under a custom/related-party tag the companyfacts "
                       f"API can't see, so long-term debt & TEV are probably UNDERSTATED.")
                # Verify against the PRIMARY source: read the actual 10-Q balance sheet (general).
                try:
                    acc = (li.get("latest_10Q") or {}).get("accession")
                    vr = vf.verify_liabilities(li.get("cik"), acc) if acc else {}
                    dl = [(l, v) for (l, v) in vr.get("debt_like_rows", []) if v]
                    if dl:
                        dtot = sum(v for _, v in dl)
                        lines = "; ".join(f"{l} ${v/1e6:,.0f}mm" for l, v in dl)
                        msg += (f" Reading the 10-Q balance sheet finds debt-like liabilities totaling "
                                f"~${dtot/1e6:,.0f}mm [{lines}] — verify (exclude equity-linked items such "
                                f"as warrants per the house definition), then re-run with "
                                f"--debt \"{T}={dtot/1e6:.0f}\".")
                    else:
                        msg += f" Read the 10-Q balance sheet, then re-run with --debt \"{T}=<$mm>\"."
                except Exception:
                    msg += f" Read the 10-Q balance sheet, then re-run with --debt \"{T}=<$mm>\"."
                flags.insert(0, msg)
        seq = val("stockholders_equity")
        if seq is not None and seq < 0:
            flags.append(f"Negative book equity (${seq/1e6:,.0f}mm) — book-insolvent; EV is entirely "
                         f"market-cap-driven. Scrutinize the liability structure.")

        L = {k: li["ltm"][k]["value"] for k in li["ltm"]}
        ebit = L.get("operating_income_ebit")
        da = L.get("depreciation_amortization")
        ebitda = li.get("ltm_ebitda_derived")
        cfo = L.get("cfo")
        ni = L.get("net_income")
        rev = L.get("revenue")
        if ebit is None:
            flags.append("Operating income (EBIT) not found — EBIT/EBITDA multiples blank.")
        if da is None:
            flags.append("D&A not found via standard tags — EBITDA may be understated; verify.")
        is_financial = (ca is None and cl is None and ebit is None)
        if is_financial:
            flags.insert(0, "FINANCIAL ISSUER (bank/insurer): no classified balance sheet and no "
                            "operating income. The working-capital EV definition and EV/EBIT & "
                            "EV/EBITDA multiples do NOT fit financials — exclude from the comp set or "
                            "use a financials framework (P/E, P/TBV, P/B). Treat any EV figure here as "
                            "unreliable for this name.")

        c = cons["consensus"].get(T, ci.blank_record())
        ntm = {"ebitda": c.get("ntm_ebitda"), "ebit": c.get("ntm_ebit"),
               "cfo": c.get("ntm_cfo"), "net_income": c.get("ntm_net_income")}

        # multiples (TEV in $, denominators in $ -> unitless)
        mult = {
            "ev_ebitda_ltm": _safe_mult(tev, ebitda),
            "ev_ebit_ltm": _safe_mult(tev, ebit),
            "ev_cfo_ltm": _safe_mult(tev, cfo),
            "ev_ni_ltm": _safe_mult(tev, ni),
            "ev_ebitda_ntm": _safe_mult(tev, ntm["ebitda"]),
            "ev_ebit_ntm": _safe_mult(tev, ntm["ebit"]),
            "ev_cfo_ntm": _safe_mult(tev, ntm["cfo"]),
            "ev_ni_ntm": _safe_mult(tev, ntm["net_income"]),
        }
        pe_ltm = _safe_mult(market_equity, ni) if include_pe else None

        companies[T] = {
            "title": li["title"], "cik": li["cik"], "fiscalYearEnd": li.get("fiscalYearEnd"),
            "is_financial": is_financial,
            "filing_10q": li["latest_10Q"], "filing_10k": li["latest_10K"],
            "price": p, "price_as_of": price.get("as_of"), "price_source": price.get("source"),
            "price_source_url": price.get("source_url"),
            # display values ($mm / mm / x)
            "shares_mm": _mm(shares),
            "market_equity_mm": _mm(market_equity),
            "lt_debt_mm": _mm(lt_debt), "finance_lease_mm": _mm(fin_lease),
            "minority_mm": _mm(minority),
            "current_assets_mm": _mm(ca), "current_liabilities_mm": _mm(cl),
            "working_capital_mm": _mm(wc), "cash_mm": _mm(val("cash_and_equivalents")),
            "tev_mm": _mm(tev),
            "ltm_mm": {"revenue": _mm(rev), "ebit": _mm(ebit), "da": _mm(da),
                       "ebitda": _mm(ebitda), "cfo": _mm(cfo), "net_income": _mm(ni)},
            "ntm_mm": {k: ntm[k] for k in ntm},  # consensus already in $mm
            "ntm_source": c.get("source"), "ntm_as_of": c.get("as_of"), "ntm_provided": c.get("_provided"),
            "multiples": mult, "pe_ltm": pe_ltm,
            "citations": {k: (ev.get(k) or {}).get("citation") for k in ev},
            "ltm_components": {k: li["ltm"][k].get("components") for k in li["ltm"]},
            "flags": flags,
        }

    return {
        "as_of_date": as_of,
        "currency": "USD",
        "units": "$ in millions; shares in millions; multiples in x",
        "methodology": "House EV = mkt equity + LT debt + finance leases + minority interest - working capital",
        "consensus_mode": consensus_mode,
        "tickers": [t.upper() for t in valid],
        "companies": companies,
        "errors": errors,
        "needs_consensus_for": cons["needs_consensus_for"],
        "consensus_source_file": cons["source_file"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--out", default=cf.fe.DEFAULT_CACHE,
                    help="cache dir for EDGAR JSON (defaults to a writable temp dir, so the skill runs "
                         "in place even when its own folder is read-only)")
    ap.add_argument("--consensus", help="path to consensus JSON (NTM)")
    ap.add_argument("--consensus-mode", default="skip",
                    choices=["capiq_excel", "manual", "skip"],
                    help="skip (default) = LTM-only, NTM blank (no subscription needed); "
                         "capiq_excel = live =CIQ() NTM formulas (needs CapIQ add-in); "
                         "manual = static NTM from --consensus JSON")
    ap.add_argument("--xlsx", help="also render an Excel workbook to this path")
    ap.add_argument("--shares", help='override shares outstanding for multi-class/Up-C names, '
                    'e.g. "OWL=675802413,ARES=222028421" (Class A from the 10-Q cover)')
    ap.add_argument("--prices", help='supply prices (for no-egress runs, or to pin a price), '
                    'e.g. "AAPL=307.34,MSFT=416.67"')
    ap.add_argument("--debt", help='override long-term debt IN $MM when it is under custom/related-party '
                    'tags the XBRL pull misses (verify in the 10-Q first), e.g. "TKR=1234.5"')
    ap.add_argument("--json", action="store_true", help="print the assembled structure as JSON")
    args = ap.parse_args(argv)

    def _parse_kv(s, num=True):
        d = {}
        for pair in (s or "").split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                d[k.strip().upper()] = float(v.strip().replace(",", "")) if num else v.strip()
        return d

    overrides = _parse_kv(args.shares)
    price_overrides = _parse_kv(args.prices)
    debt_overrides = {k: v * 1_000_000.0 for k, v in _parse_kv(args.debt).items()}  # --debt is in $mm

    comps = assemble(args.tickers, args.out, consensus_path=args.consensus,
                     consensus_mode=args.consensus_mode, shares_override=overrides,
                     prices_override=price_overrides, debt_override=debt_overrides)

    for e in comps.get("errors", []):
        print(f"  DROPPED {e['ticker']}: {e['error']}")

    if args.xlsx:
        import build_comps_xlsx as bx
        path = bx.render(comps, args.xlsx)
        print("Wrote workbook:", path)
    if args.json or not args.xlsx:
        print(json.dumps(comps, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
