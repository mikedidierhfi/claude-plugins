# Phase 05 — Denominators (LTM from filings + NTM consensus)

See [core/denominator_definitions.md](../core/denominator_definitions.md) and
[core/ltm_methodology.md](../core/ltm_methodology.md).

**LTM (from filings)** — automatic in `build_comps.py`: EBIT, EBITDA (=EBIT+D&A), CFO, Net income,
each via the FY + YTD − prior-YTD bridge, fully cited. Revenue carried for context.

**NTM (consensus)** — per [core/consensus_sourcing.md](../core/consensus_sourcing.md):
- `--consensus-mode capiq_excel` (default): NTM rows are live `=CIQ("TKR","IQ_*_EST",IQ_NTM)` formulas.
- `--consensus-mode manual --consensus consensus.json`: write a template
  (`python assets/consensus_input.py <TICKERS> --template consensus.json`), user fills it, re-run.
- `--consensus-mode skip`: leave NTM blank (LTM side still complete).

**Watch for:** negative/zero LTM denominators (loss-makers) → multiple shows `nm`; thin CFO consensus
coverage (`IQ_CFO_EST` may be blank); always footnote the consensus provider + as-of date.
