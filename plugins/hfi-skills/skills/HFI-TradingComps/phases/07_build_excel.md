# Phase 07 — Build the Excel workbook

**One command does the whole run** (fetch → compute → render):
```
python assets/build_comps.py <TICKERS> --consensus-mode capiq_excel \
       --xlsx "<output folder>/Trading_Comps_<TICKERS>_<date>.xlsx"
```
Add `--consensus consensus.json --consensus-mode manual` to embed pasted consensus instead of CIQ formulas.

`assets/build_comps_xlsx.py` renders a formula-driven workbook:
- Tickers across the top; line items down the side, building to **TEV**.
- Sections: Market data → EV bridge → LTM operating metrics → NTM consensus → Valuation multiples (x).
- Derived cells (market equity, working capital, TEV, EBITDA, every multiple, P/E memo) are **live
  Excel formulas**; NTM rows are live `=CIQ()` formulas; NTM multiples reference the CIQ cells.
- Footnotes block: per-company filings (accession/period/URL), price source+timestamp, consensus
  source, methodology notes, and any ⚠ flags.

Output naming: `Trading_Comps_<TICKERS>_<YYYY-MM-DD>.xlsx` in the user's working folder (confirm in intake).
Then go to [Phase 08 QA](08_qa.md) before delivering.
