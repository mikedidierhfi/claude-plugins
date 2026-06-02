# HFI Claude plugins

HFI Capital Management's internal Claude plugin marketplace. One private repo that distributes our Claude plugins to the team, so people install once and get updates automatically instead of being handed a file each time.

This repo holds plugin **config and skills only**. It does not contain any server code. The deal tools live in a separate Cloud Run service; the `hfi-deals` plugin just points Claude at that service's URL and signs each person in with their HFI Google account. That is why this repo is safe to distribute and why it is kept separate from the `deal-intake` server repo.

## What's in here

```
.claude-plugin/marketplace.json   the marketplace manifest (lists published plugins)
plugins/
  hfi-deals/                      connects Claude to the deal pipeline (MCP, OAuth sign-in)
  hfi-skills/                     scaffold for HFI-authored skills (not yet published)
docs/
  it-request-email.md             the note to IT to stand up org distribution
```

## How teammates install it

**Cowork / Claude Desktop (most of the team, including non-engineers).** This is the auto-updating path and the reason the repo exists. It requires a one-time org setup by an admin: connect this private repo as an organization plugin marketplace in the Claude org settings, assign it to the team, and turn on "sync automatically." After that, members install `hfi-deals` from the in-app plugin browser and updates flow whenever a change merges here. See `docs/it-request-email.md` for the exact asks.

**Claude Code CLI (engineers).** Anyone with git access to this repo can:

```
/plugin marketplace add hfi/claude-plugins
/plugin install hfi-deals@hfi
```

Auto-update is off by default per marketplace; toggle "sync automatically" or run `/plugin marketplace update hfi`.

**Manual fallback (no org setup yet).** Until the org marketplace is connected, a teammate can install the plugin from a packaged file handed to them directly. That path does not auto-update.

## Release model

- Each plugin carries a `version` in its `.claude-plugin/plugin.json`. Bump it when you want installed copies to pick up changes. Keep `version` in the plugin manifest only, not in the marketplace entry, so there is one source of truth.
- Because this repo is separate from `deal-intake`, publishing a plugin update never triggers a production deploy and vice versa.
- There is no per-user approval gate on auto-update: a merge here ships to everyone with the marketplace installed. Review changes before merging accordingly.

## Adding a new plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Add whatever the plugin provides: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` (a single `.mcp.json` may declare more than one MCP server).
3. List it in `.claude-plugin/marketplace.json` under `plugins`.
4. Commit. On the next sync, the team gets it.

See `plugins/hfi-skills/skills/README.md` for the skills convention.

## Notes

- No secrets live in this repo. The `hfi-deals` MCP authenticates each user by Google sign-in; access is gated by the server's allowlist (`UI_ALLOWED_EMAILS`), not by anything in the plugin.
- Cowork organization marketplaces must be a private/internal repo and reference plugins by relative path (as this one does). Confirm the current Cowork admin flow when connecting.
