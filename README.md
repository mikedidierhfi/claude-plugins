# HFI plugins

HFI Capital Management's plugin marketplace for Claude, Codex and ChatGPT. One repo that distributes HFI's plugins, so people install once and get updates automatically instead of being handed a file each time.

This repo holds plugin config and skills only. It contains no server code and no secrets. The deal tools run as a separate remote service; the `hfi-deals` plugin points Claude at that service and signs each person in with their HFI Google account. Access is gated by the service's own allowlist, not by anything in this repo.

## What's in here

```
.claude-plugin/marketplace.json   marketplace manifest for Claude (Cowork, Desktop, Code)
.agents/plugins/marketplace.json  marketplace manifest for Codex and ChatGPT
plugins/
  hfi-deals/                      connects the assistant to the deal pipeline (MCP, OAuth sign-in);
                                  .claude-plugin/ and .codex-plugin/ manifests share one .mcp.json
  hfi-skills/                     HFI-authored skills (Claude today)
```

## How to install

**Cowork / Claude Desktop.** In the plugin manager, add this marketplace (Add marketplace, then `mikedidierhfi/claude-plugins`), install `hfi-deals`, and restart. You need a paid Claude plan. Once added, updates flow automatically.

**Claude Code CLI.**

```
/plugin marketplace add mikedidierhfi/claude-plugins
/plugin install hfi-deals@hfi
```

Run `/plugin marketplace update hfi` to pull the latest, or toggle automatic sync.

**Codex (app, CLI, IDE).** Add the marketplace once from a terminal, then install from the Plugins page in the Codex app (or `/plugins` in the CLI). Installing prompts for the HFI Google sign-in.

```
codex plugin marketplace add mikedidierhfi/claude-plugins
```

**ChatGPT.** The deal server is registered in ChatGPT already; `plugins/hfi-deals/.app.json` carries that registration, so the plugin works there too. Teammates do not need developer mode. In a Business or Enterprise workspace the owner publishes it once from Plugins (Personal, open the plugin's menu, Publish) to the roles that should have it, or imports this repo under Admin, Plugins, Add, Import marketplace and sets the installation policy per role. Each teammate signs in with their HFI Google account the first time.

## Release model

- Each plugin carries a `version` in its `.claude-plugin/plugin.json`. Bump it when you want installed copies to update. Keep the version in the plugin manifest only, not the marketplace entry, so there is one source of truth.
- A merge here ships to everyone who has the marketplace installed. There is no per-user approval gate on updates, so review changes before merging.

## Adding a new plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Add what the plugin provides: `skills/`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` (one `.mcp.json` may declare more than one MCP server).
3. List it in `.claude-plugin/marketplace.json`.
4. Commit. On the next sync, the team gets it.

See `plugins/hfi-skills/skills/README.md` for the skills convention.
