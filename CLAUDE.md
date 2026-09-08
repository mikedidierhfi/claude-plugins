# CLAUDE.md - working notes for this repo

## What this is

HFI Capital Management's plugin marketplace for Claude, Codex and ChatGPT. A single repo that distributes HFI's plugins so teammates install once and get updates automatically. It contains plugin config and skills only: no server code, no secrets.

Currently published: `hfi-deals`, which connects Claude to the HFI deal pipeline. The plugin is just a pointer (an `.mcp.json`) at a remote MCP service, plus docs; the service itself lives in a separate private repo. Access to the deal data is gated on that service by Google sign-in and a server-side allowlist, not by anything here.

## IMPORTANT: this repo is PUBLIC

It is published at https://github.com/mikedidierhfi/claude-plugins so non-technical teammates can add it in Cowork without a GitHub account. Because it is public:

- Never commit secrets, tokens, or credentials.
- Keep all docs and examples sanitized: no real deal names, sponsor names, teammate names, internal service or repo names, email addresses, or allowlist contents.
- The MCP URL in `.mcp.json` is intentionally public and safe to expose; it is gated by sign-in on the server side.

## Layout

```
.claude-plugin/marketplace.json   Claude marketplace manifest (marketplace name: "hfi")
.agents/plugins/marketplace.json  Codex / ChatGPT marketplace manifest (same name, same plugins)
plugins/
  hfi-deals/                       the deal pipeline plugin: .claude-plugin/plugin.json and
                                   .codex-plugin/plugin.json both point at the one .mcp.json
  hfi-skills/                      HFI-authored skills (Claude manifest only so far)
.claude/settings.json             commit attribution disabled
```

The `.mcp.json` shape (`mcpServers` -> `{type: "http", url}`) is what Claude and Codex both read, so keep a single file. ChatGPT itself does not run a bundled `.mcp.json`; it uses the MCP connection registered once in developer mode, whose id lives in `plugins/hfi-deals/.app.json`. Re-registering the server in ChatGPT changes that id; update the file.

## Releasing an update

- Bump `version` in the plugin's `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`. Keep `version` in the plugin manifests only, not the marketplace entries, so there is one source of truth per surface.
- A push to `main` ships to everyone who has the marketplace installed. There is no per-user approval gate, so review before pushing.
- This repo is deliberately separate from the deal pipeline service repo, so publishing a plugin update never triggers anything on the service side and vice versa.

## Adding a plugin or skill

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json` (and a `.codex-plugin/plugin.json` if it should reach Codex / ChatGPT).
2. Add what it provides: `skills/<name>/SKILL.md`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` (one file may declare more than one MCP server).
3. List it in `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json`.
4. Commit and push.

Only put HFI-original skills here. Anthropic's prebuilt skill packs come from their own marketplaces; do not copy that content in.

## Git

This is a personal public repo (owner: mikedidierhfi). Normal commit flow on `main`. Attribution trailers are off via `.claude/settings.json`.
