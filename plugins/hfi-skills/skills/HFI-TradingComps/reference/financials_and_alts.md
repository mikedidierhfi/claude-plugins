# Financials & alternative asset managers — recognize them, switch frameworks

The house EV/EBITDA methodology is built for **operating companies**. It does **not** fit
financials or alternative asset managers. Recognize them early and switch tools — don't hand the
user a TEV/EBITDA table full of blanks and call it done.

## How to recognize them (the engine flags this automatically)
- **No classified balance sheet** — `AssetsCurrent` / `LiabilitiesCurrent` are absent (so no
  working capital). → engine omits WC + flags.
- **No `OperatingIncomeLoss`** — no GAAP operating-income line (so no EBIT/EBITDA). → multiples blank.
- When BOTH are true the engine sets `is_financial` and emits a loud flag.
- **Alt managers specifically** (BX, KKR, ARES, OWL, APO, CG, TPG, BAM, etc.): the above PLUS an
  **Up-C / multi-class** structure — Class A trades, but most economics sit in operating-group
  units booked as noncontrolling interest (NCI). Symptoms seen in this skill:
  - Shares outstanding missing/stale in XBRL default series (class-split) → use `--shares` (below).
  - Huge `MinorityInterest` (e.g., KKR ~$47.5B incl. consolidated insurance/funds) — adding it to
    EV inflates TEV meaninglessly. CFO is volatile/negative (consolidated fund flows).

## Banks / insurers
EV/working-capital and EV/EBITDA are meaningless. Use **P/E, P/tangible-book (P/TBV), P/B**, ROTCE.
Exclude from an operating-company comp set or build a financials-specific sheet.

## Alternative asset managers — the right framework
Value them on **AUM growth, Fee-Related Earnings (FRE), and Distributable Earnings (DE)** — not EV.
Key metrics & where to get them (all primary, no CapIQ needed):

| Metric | Notes | Source |
|---|---|---|
| AUM, Fee-Paying AUM | scale | quarterly **earnings release** (8-K EX-99.1/99.2) |
| **FRE** (Fee-Related Earnings) | the cleanest cross-firm earnings metric | earnings release |
| **Distributable** earnings | name differs: **BX/OWL** = Distributable Earnings; **ARES** = (After-tax) Realized Income; **KKR** = Adjusted Net Income (ANI) | earnings release |
| FRE/sh, DE(or equiv)/sh | firms publish per-(adjusted)-share | earnings release |
| GAAP NI to public co., GAAP EPS | for a (caveated) GAAP P/E | 10-Q (our engine already pulls LTM) |
| Class A & economic/adjusted shares | economic = Class A + operating-group units | 10-Q cover + earnings release |

**Multiples:** `P/E (GAAP)`, `P/FRE = price ÷ LTM FRE/sh`, `P/Distributable = price ÷ LTM DE-equiv/sh`,
`economic mkt cap ÷ AUM (%)`. **Ignore GAAP P/E as the primary read** — Up-C makes NI-to-public a
sliver, so GAAP P/E looks inflated (e.g., ARES ~53×). FRE/DE multiples are the real lens.

## How to build it (tools now in the skill)
1. `python assets/fetch_earnings.py <TICKER> --grep "Fee Related Earnings" "Distributable Earnings" "Assets Under Management" "per share"`
   → pulls the latest earnings release (8-K EX-99) text so you can read the AUM/FRE/DE/per-share figures.
2. Get Class-A share counts from the 10-Q cover; pass them to the EV engine when needed via
   `build_comps.py --shares "OWL=675802413,ARES=222028421"` (Class A; flag notes economic value
   includes operating-group units).
3. Fill the per-company dict and call `assets/alt_manager_comp.py: render(data, out)` (it has a
   worked OWL/ARES/BX/KKR Q1'26 example — run `python assets/alt_manager_comp.py out.xlsx`).
4. Footnote every figure to the specific earnings release + 10-Q. State that it's a screening comp
   (FRE/DE/RI/ANI are non-GAAP and not perfectly uniform across firms).

## Worked precedent (2026-06-07, Q1'26 data)
OWL/ARES/BX/KKR: P/FRE 9.9× / 22.3× / 23.5× / 21.5×; P/Distributable 11.4× / 23.4× / 19.8× / 18.3×;
mkt cap / AUM 4.9% / 6.4% / 10.9% / 11.1%. OWL screened cheapest; BX the scale/quality premium.
