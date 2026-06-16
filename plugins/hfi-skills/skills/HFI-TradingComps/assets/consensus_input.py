#!/usr/bin/env python3
"""
consensus_input.py — Obtain Wall Street consensus estimates for the NTM (Next-Twelve-Months)
columns and (optionally) consensus CFO. Values are in $ MILLIONS.

There is NO consensus connector wired into this environment, so this module implements a
three-tier strategy and degrades gracefully:

  (1) CONNECTOR HOOK  — fetch_consensus_via_connector(): if a market-data MCP (CapIQ, FactSet,
      Bloomberg, Visible Alpha, Koyfin, etc.) is ever connected, wire it here. Today it returns
      None so the skill falls through to (2)/(3). See core/consensus_sourcing.md.
  (2) MANUAL / CHROME FILE — a JSON file the analyst fills (by hand, or populated by reading a
      provider screen via Chrome). load_consensus(path=...) reads it.
  (3) BLANKS + FLAG   — if neither is available, NTM cells stay blank and the run reports exactly
      which tickers still need consensus and what login would supply it.

Per-ticker schema (all monetary values in $mm):
  {
    "ntm_ebitda": 175000, "ntm_ebit": 160000, "ntm_cfo": 150000, "ntm_net_income": 135000,
    "source": "Koyfin consensus (mean)", "as_of": "2026-06-05"
  }
"""
import argparse, json, os

NTM_KEYS = ("ntm_ebitda", "ntm_ebit", "ntm_cfo", "ntm_net_income")


def fetch_consensus_via_connector(ticker):
    """Placeholder for a future market-data MCP. Return a dict matching the schema, or None.

    To wire a provider when one is connected:
      - discover it with ToolSearch (keywords: capiq / factset / bloomberg / estimates / consensus)
      - call its 'consensus estimates' tool for `ticker`
      - map NTM mean EBITDA / EBIT / CFO / net income into the schema below (convert to $mm)
    Returns None today (no provider connected)."""
    return None


def blank_record():
    return {k: None for k in NTM_KEYS} | {"source": None, "as_of": None, "_provided": False}


def load_consensus(tickers, path=None, fmp_key=None):
    """Tier 1 (connector) -> Tier 1b (FMP API, if a key is supplied) -> Tier 2 (file) -> Tier 3
    (blank). Returns {consensus, needs, source}."""
    file_data = {}
    src = None
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            file_data = json.load(f)
        src = path

    fmp_data, fmp_notes = {}, {}
    if fmp_key:
        try:
            import fmp_consensus as fc
            fmp_data, fmp_notes = fc.fetch_ntm(tickers, fmp_key)
            src = src or "FMP analyst consensus (NTM, calendarized)"
        except Exception:
            fmp_data, fmp_notes = {}, {}

    out, needs = {}, []
    for t in tickers:
        T = t.upper()
        rec = fetch_consensus_via_connector(T)  # tier 1
        if rec is None:
            rec = fmp_data.get(T)                # tier 1b (FMP)
        if rec is None:
            rec = file_data.get(T)               # tier 2
        if rec and any(rec.get(k) is not None for k in NTM_KEYS):
            rec = {**blank_record(), **rec, "_provided": True}
            out[T] = rec
        else:
            out[T] = blank_record()              # tier 3
            needs.append(T)
    return {"consensus": out, "source_file": src, "needs_consensus_for": needs,
            "fmp_notes": fmp_notes}


def write_template(tickers, path):
    """Write a blank consensus JSON for the analyst to fill (manual/Chrome path)."""
    tmpl = {t.upper(): {**{k: None for k in NTM_KEYS},
                        "source": "<provider, e.g. Koyfin/FactSet mean>", "as_of": "<YYYY-MM-DD>"}
            for t in tickers}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tmpl, f, indent=2)
    return path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--template", help="write a blank consensus template JSON to this path")
    ap.add_argument("--file", help="load/validate consensus from this JSON path")
    args = ap.parse_args(argv)
    if args.template:
        print("Wrote template:", write_template(args.tickers, args.template))
    print(json.dumps(load_consensus(args.tickers, args.file), indent=2))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
