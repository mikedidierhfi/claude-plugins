# Phase 01 — Intake & prompting

Goal: end this phase with a confirmed **run config** — the tickers to compare and a few options.
This is the moment the skill "prompts the user for which companies to compare."

## Step 1 — Get the tickers
- If the user already named companies/tickers in their request, use those (resolve company names
  to tickers; confirm any you inferred).
- **If no tickers were given, ask — plainly and directly:**

  > "Which public companies would you like to compare? Send me the ticker symbols, separated by
  > commas (e.g., `AAPL, MSFT, GOOGL`). I can do 2–10 at a time."

  Tickers are free-form, so ask in prose (don't force them into multiple-choice). Accept company
  names too and map them to tickers.
- **Validate** each ticker before proceeding: run
  `python assets/fetch_edgar.py <TICKERS>`. Any ticker that fails to resolve to a CIK, or that has
  no 10-Q/10-K (foreign private issuers file 20-F/40-F, not 10-K/10-Q — flag these; this skill
  targets domestic SEC filers), gets surfaced to the user: *"I couldn't find SEC 10-Q/10-K filings
  for X — is it a foreign filer or a different ticker?"* Do not silently drop a name.

## Step 2 — Confirm options (one `AskUserQuestion` call, up to 4 questions)
Ask only if it matters; use sensible defaults and state them. Suggested questions:
1. **Consensus / NTM data** — "How should I get the Next-Twelve-Months Wall Street consensus?"
   - *"I'll paste it (recommended)"* → you'll generate a template for them to fill (see Phase 05).
   - *"Pull via Chrome from my logged-in provider"* → name the provider; use Chrome in Phase 05.
   - *"Skip NTM — LTM only"* → leave NTM blank (workbook still complete on the LTM side).
2. **Operating leases** — "Include operating-lease liabilities in EV?" Default **No** (capital/finance
   leases only, per the house definition). Yes = add non-current operating lease liability (footnoted).
3. **P/E memo row** — "Include a P/E (market cap ÷ net income) memo row?" Default **Yes**.
4. **Units** — "$ in millions (default) or $ in billions?"

(If a dual-class issuer is in the set — e.g., GOOG/GOOGL, BRK.A/BRK.B — add a question or confirm:
"For <issuer>, sum all share classes × their prices, or use the primary class only?" Default: sum
all classes. See `reference/common_mistakes.md`.)

## Step 3 — Build the run config
Assemble (and echo back a one-line confirmation before running):
```json
{
  "tickers": ["AAPL", "MSFT"],
  "as_of_date": "<today>",
  "consensus_mode": "paste | chrome | skip",
  "consensus_provider": "<if chrome/paste>",
  "include_operating_leases": false,
  "include_pe_memo": true,
  "units": "mm",
  "output_path": "<working folder>/Trading_Comps_<TICKERS>_<date>.xlsx"
}
```
Confirm succinctly, e.g.: *"Comparing AAPL, MSFT, GOOGL — house EV multiples, LTM from filings,
NTM you'll paste, $mm. Building now."* Then proceed to **Phase 02**.

## Tone
You are the analyst. Be crisp and senior: confirm scope, note any judgment calls (dual class,
financials that don't fit the WC definition), and get to work. Don't over-question — one options
prompt is enough.
