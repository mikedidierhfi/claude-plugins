#!/usr/bin/env python3
"""
company_facts.py — Turn cached SEC companyfacts into the exact line items this skill needs,
each with a citation, plus LTM (last-twelve-months) figures for flow concepts.

Depends only on stdlib + fetch_edgar.py (same folder) for cik/filing resolution.

LTM bridge:  LTM = latest fiscal-year (10-K) + latest YTD (10-Q) - prior-year comparable YTD.
If the most recent filing is a 10-K (no newer 10-Q), LTM = the fiscal-year value.

Usage:
  python company_facts.py AAPL
  python company_facts.py AAPL --out ./_cache
"""
import argparse, datetime as dt, json, os, sys

import fetch_edgar as fe

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "xbrl_tags.json"), "r", encoding="utf-8") as _f:
    TAGS = json.load(_f)


def _d(s):
    return dt.date.fromisoformat(s)


def concept_records(facts, taxonomy, tag):
    """Return flat list of unit records for a concept, tagged with their unit key."""
    node = facts.get("facts", {}).get(taxonomy, {}).get(tag)
    if not node:
        return []
    out = []
    for unit_key, recs in node.get("units", {}).items():
        for r in recs:
            rr = dict(r)
            rr["_unit"] = unit_key
            rr["_tag"] = tag
            rr["_taxonomy"] = taxonomy
            out.append(rr)
    return out


def _cite(r):
    return {
        "tag": f'{r.get("_taxonomy")}:{r.get("_tag")}',
        "unit": r.get("_unit"),
        "start": r.get("start"),
        "end": r.get("end"),
        "form": r.get("form"),
        "fy": r.get("fy"),
        "fp": r.get("fp"),
        "filed": r.get("filed"),
        "accn": r.get("accn"),
        "frame": r.get("frame"),
        "val": r.get("val"),
    }


# ---------- instant (balance-sheet) resolution ----------
def resolve_instant(facts, item_key, target_end, latest_end=False, end_tol_days=7,
                    max_stale_days=400, future_tol_days=80):
    """Resolve a balance-sheet (point-in-time) line item to the value at/near `target_end`.

    STALENESS GUARD: only accept records whose period-end falls in the window
    [target - max_stale_days, target + future_tol_days]. This rejects dangerous multi-year-old
    fallbacks (e.g., a 2014 long-term-debt or 2011 share count that some issuers leave in the
    XBRL 'default' series) while still allowing an annual-only value carried from the most recent
    10-K (up to ~13 months old). If no tag yields a fresh value, returns missing (+ a note that a
    stale-only value existed, for diagnostics). Never silently returns a years-old number."""
    spec = TAGS[item_key]
    target = _d(target_end) if target_end else None
    stale_seen = None
    for t in spec["tags"]:
        recs = [r for r in concept_records(facts, t["taxonomy"], t["tag"]) if r.get("end")]
        if not recs:
            continue
        if target is None:
            recs.sort(key=lambda r: (r["end"], r.get("filed", "")))
            best = recs[-1]
            return {"value": best["val"], "citation": _cite(best)}
        lo = target - dt.timedelta(days=max_stale_days)
        hi = target + dt.timedelta(days=future_tol_days)
        inwin = [r for r in recs if lo <= _d(r["end"]) <= hi]
        if not inwin:
            recs.sort(key=lambda r: r["end"])
            if stale_seen is None:
                stale_seen = recs[-1]
            continue
        if latest_end:
            inwin.sort(key=lambda r: (r["end"], r.get("filed", "")))
            best = inwin[-1]
        else:
            inwin.sort(key=lambda r: (abs((_d(r["end"]) - target).days), r.get("filed", "")))
            best = inwin[0]
        out = {"value": best["val"], "citation": _cite(best)}
        if abs((_d(best["end"]) - target).days) > max(end_tol_days, 40):
            out["approx"] = True  # e.g. carried from the latest 10-K, not the latest 10-Q
        return out
    res = {"value": None, "citation": None, "missing": True}
    if stale_seen is not None:
        res["stale_only"] = (f'{stale_seen.get("_taxonomy")}:{stale_seen.get("_tag")} '
                             f'end={stale_seen.get("end")} ignored (older than {max_stale_days}d)')
    return res


# ---------- duration (flow) resolution & LTM ----------
def _durations(facts, item_key, fresh_after=None):
    """Duration records for the first fallback tag that yields data. If `fresh_after` (a date) is
    given, prefer the first tag that has at least one record ending on/after it — avoids locking onto
    a tag whose only data is years stale when a later fallback tag holds current values. Falls back
    to whatever stale records exist (which simply won't date-match in _pick -> graceful degrade)."""
    spec = TAGS[item_key]
    stale = []
    for t in spec["tags"]:
        recs = []
        for r in concept_records(facts, t["taxonomy"], t["tag"]):
            if r.get("start") and r.get("end"):
                r["_days"] = (_d(r["end"]) - _d(r["start"])).days
                recs.append(r)
        if recs:
            if fresh_after is None or any(_d(r["end"]) >= fresh_after for r in recs):
                return recs
            stale = stale or recs
    return stale


def _pick(records, end_target, dmin, dmax, end_tol=10):
    cands = [r for r in records
             if dmin <= r["_days"] <= dmax and abs((_d(r["end"]) - _d(end_target)).days) <= end_tol]
    if not cands:
        return None
    # prefer the longest period (YTD over single quarter), then latest filed
    cands.sort(key=lambda r: (r["_days"], r.get("filed", "")))
    return cands[-1]


def compute_ltm(facts, item_key, fy_end, q_end):
    """LTM = FY(10-K) + YTD(10-Q, ending q_end) - prior-year YTD."""
    anchor = max([d for d in (q_end, fy_end) if d], default=None)
    fresh_after = (_d(anchor) - dt.timedelta(days=420)) if anchor else None
    recs = _durations(facts, item_key, fresh_after=fresh_after)
    if not recs:
        return {"value": None, "components": {}, "missing": True}

    fy = _pick(recs, fy_end, 350, 380)
    # If no separate quarter (latest filing is the 10-K), LTM is just the FY.
    if not q_end or (_d(q_end) <= _d(fy_end)):
        if fy:
            return {"value": fy["val"], "method": "FY", "components": {"fy": _cite(fy)}}
        return {"value": None, "components": {}, "missing": True}

    # Current YTD ending at q_end (longest sub-annual period ending there)
    ytd = _pick(recs, q_end, 45, 330)
    prior_end = (_d(q_end) - dt.timedelta(days=365)).isoformat()  # ~1yr earlier; leap-safe
    prior = None
    if ytd:
        d = ytd["_days"]
        prior = _pick(recs, prior_end, d - 12, d + 12)

    if fy and ytd and prior:
        val = fy["val"] + ytd["val"] - prior["val"]
        return {"value": val, "method": "FY + YTD - priorYTD",
                "components": {"fy": _cite(fy), "ytd": _cite(ytd), "prior_ytd": _cite(prior)}}
    # Degrade gracefully with whatever we have
    if fy:
        return {"value": fy["val"], "method": "FY only (YTD/prior incomplete)",
                "components": {"fy": _cite(fy),
                               "ytd": _cite(ytd) if ytd else None,
                               "prior_ytd": _cite(prior) if prior else None},
                "warn": "LTM degraded to FY; could not match YTD/prior cleanly"}
    return {"value": None, "components": {}, "missing": True}


def compute_line_items(facts, q_end, fy_end, ticker=None, title=None, cik=None,
                       fiscal_year_end=None, q_meta=None, k_meta=None):
    """Pure computation: given XBRL `facts` and the latest 10-Q/10-K period-ends, return all EV
    line items + LTM figures. No network. This is the deterministic core the tests exercise."""
    ev = {
        "shares_outstanding": resolve_instant(facts, "shares_outstanding", q_end, latest_end=True),
        "long_term_debt_noncurrent": resolve_instant(facts, "long_term_debt_noncurrent", q_end),
        "finance_lease_noncurrent": resolve_instant(facts, "finance_lease_noncurrent", q_end),
        "minority_interest": resolve_instant(facts, "minority_interest", q_end),
        "current_assets": resolve_instant(facts, "current_assets", q_end),
        "current_liabilities": resolve_instant(facts, "current_liabilities", q_end),
        "cash_and_equivalents": resolve_instant(facts, "cash_and_equivalents", q_end),
        # for the liabilities-completeness reconciliation (catches debt under custom/related-party tags)
        "total_liabilities": resolve_instant(facts, "total_liabilities", q_end),
        "liabilities_noncurrent": resolve_instant(facts, "liabilities_noncurrent", q_end),
        "operating_lease_noncurrent": resolve_instant(facts, "operating_lease_noncurrent_optional", q_end),
        "deferred_tax_noncurrent": resolve_instant(facts, "deferred_tax_noncurrent", q_end),
        "other_liabilities_noncurrent": resolve_instant(facts, "other_liabilities_noncurrent", q_end),
        "stockholders_equity": resolve_instant(facts, "stockholders_equity", q_end),
    }
    ltm = {
        "revenue": compute_ltm(facts, "revenue", fy_end, q_end),
        "operating_income_ebit": compute_ltm(facts, "operating_income_ebit", fy_end, q_end),
        "depreciation_amortization": compute_ltm(facts, "depreciation_amortization", fy_end, q_end),
        "net_income": compute_ltm(facts, "net_income", fy_end, q_end),
        "cfo": compute_ltm(facts, "cfo", fy_end, q_end),
    }
    # Derived
    ebit = ltm["operating_income_ebit"]["value"]
    da = ltm["depreciation_amortization"]["value"]
    ltm_ebitda = (ebit + da) if (ebit is not None and da is not None) else None

    wc = None
    ca = ev["current_assets"]["value"]
    cl = ev["current_liabilities"]["value"]
    if ca is not None and cl is not None:
        wc = ca - cl

    return {
        "ticker": ticker, "title": title, "cik": cik,
        "fiscalYearEnd": fiscal_year_end,
        "latest_10Q": q_meta or {}, "latest_10K": k_meta or {},
        "ev_line_items": ev,
        "working_capital": wc,
        "ltm": ltm,
        "ltm_ebitda_derived": ltm_ebitda,
    }


def build_line_items(ticker, cache_dir):
    """Network path: fetch filings + facts from EDGAR, then compute. Used in production runs."""
    meta = fe.fetch_ticker(ticker, cache_dir)
    facts = fe.get_companyfacts(meta["cik"], cache_dir)
    q = meta.get("latest_10Q") or {}
    k = meta.get("latest_10K") or {}
    return compute_line_items(
        facts, q.get("reportDate"), k.get("reportDate"),
        ticker=meta["ticker"], title=meta["title"], cik=meta["cik"],
        fiscal_year_end=meta["fiscalYearEnd"], q_meta=q, k_meta=k)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--out", default=fe.DEFAULT_CACHE)
    ap.add_argument("--full", action="store_true", help="include full citations")
    args = ap.parse_args(argv)
    res = []
    for t in args.tickers:
        try:
            res.append(build_line_items(t, args.out))
        except Exception as e:
            res.append({"ticker": t.upper(), "error": repr(e)})
    if not args.full:
        # compact: strip citation dicts to one-liners for readability
        def compact(d):
            for k, v in (d.get("ev_line_items") or {}).items():
                if isinstance(v, dict) and v.get("citation"):
                    c = v["citation"]; v["citation"] = f'{c["tag"]} end={c["end"]} form={c["form"]} accn={c["accn"]}'
            for k, v in (d.get("ltm") or {}).items():
                if isinstance(v, dict) and v.get("components"):
                    v["components"] = {kk: (f'{cc["tag"]} {cc.get("start")}->{cc["end"]} val={cc["val"]}' if cc else None)
                                       for kk, cc in v["components"].items()}
            return d
        res = [compact(r) if "error" not in r else r for r in res]
    print(json.dumps(res, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
