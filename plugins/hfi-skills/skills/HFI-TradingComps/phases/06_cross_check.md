# Phase 06 — Cross-check vs the investor presentation

The user asked that computed figures be checked against each company's **most recent investor
presentation** (IR website). This catches tagging errors and surfaces the adjusted-vs-clean gap.

## Steps
1. Find the latest deck: company **Investor Relations** site → "Events & Presentations" / "Latest
   quarterly presentation" / earnings supplement. Use Chrome (or WebSearch for the IR URL, then Chrome).
   Prefer the company's own PDF, not a third-party summary.
2. Pull the headline metrics the company reports: revenue, **Adjusted EBITDA**, operating income,
   net income, sometimes net debt / share count.
3. Compare to our computed (clean, LTM) figures. Expect differences:
   - **Adjusted EBITDA > clean EBITDA** (add-backs: SBC, restructuring, M&A) — normal; note the bridge.
   - Period mismatch: deck may show a single quarter or guidance, not LTM — align periods before judging.
4. Record the comparison: add a short cross-check note per company (deck date + URL) and, if useful,
   an optional "Company Adj. EBITDA (per IR deck)" row in the workbook, clearly labeled and cited.
5. **Surface the deck link in the chat reply.** In the "Sources & citations" block, every company MUST
   get an **"Investor materials"** line with a direct link to the deck and the exact slide/page you
   used (e.g., "Q1-FY26 earnings presentation, slide 7 — <url>"). If no current deck exists or the IR
   site is inaccessible, state that explicitly on the line. This is required output, not optional.

## Rules
- The **computed clean GAAP figure stays the default**; the company's adjusted number is shown for
  reference only, never silently substituted.
- Cite the deck (title, date, URL/page). Treat IR links like any web link (verify the domain).
- If no current deck exists, note that and rely on the filing-derived figures.

(Automation: this step is Chrome/WebFetch-driven and analyst-judged; there's no single script. Keep
it lightweight — a couple of headline metrics per name is enough to validate.)
