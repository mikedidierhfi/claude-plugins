# HFI Claude plugins

HFI Capital Management's Claude plugin marketplace. One repo that distributes HFI's Claude plugins, so people install once and get updates automatically instead of being handed a file each time.

This repo holds plugin config and skills only. It contains no server code and no secrets. The deal tools run as a separate remote service; the `hfi-deals` plugin points Claude at that service and signs each person in with their HFI Google account. Access is gated by the service's own allowlist, not by anything in this repo.

## What's in here

```
.claude-plugin/marketplace.json   the marketplace manifest (lists published plugins)
plugins/
  hfi-deals/                      connects Claude to the deal pipeline (MCP, OAuth sign-in)
  hfi-skills/                     scaffold for HFI-authored skills (not yet published)
```

## How to install

**Cowork / Claude Desktop.** In the plugin manager, add this marketplace (Add marketplace, then `mikedidierhfi/claude-plugins`), install `hfi-deals`, and restart. You need a paid Claude plan. Once added, updates flow automatically.

**Claude Code CLI.**

```
/plugin marketplace add mikedidierhfi/claude-plugins
/plugin install hfi-deals@hfi
```

Run `/plugin marketplace update hfi` to pull the latest, or toggle automatic sync.

## Release model

- Each plugin carries a `version` in its `.claude-plugin/plugin.json`. Bump it when you want installed copies to update. Keep the version in the plugin manifest only, not the marketplace entry, so there is one source of truth.
- A merge here ships to everyone who has the marketplace installed. There is no per-user approval gate on updates, so review changes before merging.

## Adding a new plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Add what the plugin provides: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` (one `.mcp.json` may declare more than one MCP server).
3. List it in `.claude-plugin/marketplace.json`.
4. Commit. On the next sync, the team gets it.

See `plugins/hfi-skills/skills/README.md` for the skills convention.
