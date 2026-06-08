# Consensus sourcing (NTM + consensus CFO) — the login-gated piece

The Next-Twelve-Months (NTM) columns and any consensus CFO require a Wall Street estimates
provider. There is **no consensus MCP/connector in this environment**, so the skill is built to
use the data the user actually has — **S&P Capital IQ** — primarily through the **Capital IQ Excel
plug-in**, with two fallbacks. (User confirmed: has CapIQ, not FactSet.)

## Tier 1 (default) — Capital IQ Excel plug-in formulas  (`consensus_mode="capiq_excel"`)
The workbook writes the NTM rows as **live `=CIQ(...)` formulas**. When the user opens the file in
Excel with the Capital IQ Office add-in active, they populate from the user's own CapIQ login — no
credentials touch this tool, and they refresh on demand.

Formula shape (verified against the S&P Capital IQ Excel Plug-in manual):
```
=CIQ("<identifier>", "<mnemonic>", IQ_NTM)
```
Mnemonics used:
| Row | Mnemonic | Confidence |
|---|---|---|
| EBITDA (NTM) | `IQ_EBITDA_EST` | Standard, well-covered |
| EBIT (NTM) | `IQ_EBIT_EST` | Standard |
| Net income (NTM) | `IQ_NI_EST` | Standard |
| CFO (NTM) | `IQ_CFO_EST` | **Thin coverage** — may return blank; verify or leave to manual |

- `IQ_NTM` is the period token the plug-in defines for next-twelve-months (sum of the next four
  quarterly estimates, or calendarized). It is written **unquoted** (it's a defined name).
- **Identifier:** a plain ticker works for most names. For multi-class/ambiguous issuers, qualify it
  (e.g. `"BRK.B"` or `"NYSE:BRK.B"`). The workbook footnote flags this.
- **If you see `#NAME?`** on open, the add-in isn't loaded/enabled → fall to Tier 2 or 3.
- Because the NTM **multiples** reference the CIQ cells, they compute automatically once estimates land.

## Tier 2 — manual paste  (`consensus_mode="manual"`, `--consensus consensus.json`)
1. `python assets/consensus_input.py <TICKERS> --template consensus.json` writes a blank template.
2. The user fills NTM EBITDA/EBIT/CFO/NI ($mm) + source + as-of (read off CapIQ, Koyfin, etc.).
3. Re-run with `--consensus consensus.json --consensus-mode manual` → values written statically, sourced.

## Tier 3 — CapIQ web via Chrome
If the user uses capitaliq.com / S&P Capital IQ Pro in a browser, drive Chrome on their logged-in
session to read the consensus mean for each metric, then write into `consensus.json` (Tier 2 path).
Always confirm the period is NTM/forward and capture the as-of date. (Suspicious-link rules apply.)

## Tier 0 (future) — a real connector
`assets/consensus_input.py: fetch_consensus_via_connector()` is the hook. If a CapIQ/estimates MCP
is ever connected, discover it via ToolSearch (keywords: capiq / capital iq / estimates / consensus),
call its estimates tool per ticker, map NTM mean EBITDA/EBIT/CFO/NI into the schema (convert to $mm),
and return it — the rest of the pipeline is unchanged.

## Always
Footnote the consensus **provider + as-of date**. Never fabricate an estimate. If a cell is blank,
leave it blank (the workbook flags "NTM pending"); do not infer it from the LTM figure.
