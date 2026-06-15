#!/usr/bin/env python3
"""
selfcheck.py — One-command health + regression check for the HFI-TradingComps skill. Run this
before relying on a comp to confirm the engine behaves identically ("same results every time"):

  python assets/selfcheck.py

Verifies the environment (Python, openpyxl), SEC EDGAR reachability (soft), and runs the full
offline regression suite (engine line items + LTM, orchestrator valuation math, Excel renderer).
Exit 0 = healthy.
"""
import os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.normpath(os.path.join(HERE, "..", "tests"))
PY = sys.executable
sys.path.insert(0, HERE)


def main():
    results = []  # (name, ok, hard, detail)

    results.append(("Python >= 3.10", sys.version_info >= (3, 10), True, sys.version.split()[0]))
    try:
        import openpyxl
        results.append(("openpyxl importable", True, True, openpyxl.__version__))
    except Exception as e:
        results.append(("openpyxl importable", False, True, repr(e)))

    # SEC EDGAR reachability — soft (uses the skill's real fetch path; cache-aware, so fast)
    try:
        import fetch_edgar as fe
        m = fe.load_ticker_map(fe.DEFAULT_CACHE)
        ok = "AAPL" in m
        results.append(("SEC EDGAR reachable (soft)", ok, False, f"{len(m):,} tickers resolved"))
    except Exception as e:
        results.append(("SEC EDGAR reachable (soft)", False, False, repr(e)[:80]))

    for tf in ("test_engine.py", "test_render.py", "test_valuation.py", "test_offline.py",
               "test_verify.py", "test_recalc.py", "test_price.py", "test_sources.py"):
        path = os.path.join(TESTS, tf)
        if not os.path.exists(path):
            results.append((tf, False, True, "missing")); continue
        r = subprocess.run([PY, path], capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or [""])[-1]
        results.append((tf, r.returncode == 0, True, last))

    print("=" * 64)
    print("HFI-TradingComps — self-check")
    print("=" * 64)
    hard_ok = True
    for name, ok, hard, detail in results:
        tag = "PASS" if ok else ("FAIL" if hard else "WARN")
        if hard and not ok:
            hard_ok = False
        print(f"  [{tag}] {name:<34} {detail}")
    print("-" * 64)
    print("HEALTHY — engine is reproducible." if hard_ok else "PROBLEM — see FAIL lines above.")
    return 0 if hard_ok else 1


if __name__ == "__main__":
    sys.exit(main())
