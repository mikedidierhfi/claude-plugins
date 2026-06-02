# CLAUDE.md - working notes for this repo

## What this is

HFI Capital Management's Claude plugin marketplace. A single repo that distributes HFI's Claude plugins so teammates install once and get updates automatically. It contains plugin config and skills only: no server code, no secrets.

Currently published: `hfi-deals`, which connects Claude to the HFI deal pipeline. The plugin is just a pointer (an `.mcp.json`) at a remote MCP service, plus docs; the service itself lives in a separate private repo. Access to the deal data is gated on that service by Google sign-in and a server-side allowlist, not by anything here.

## IMPORTANT: this repo is PUBLIC

It is published at https://github.com/mikedidierhfi/claude-plugins so non-technical teammates can add it in Cowork without a GitHub account. Because it is public:

- Never commit secrets, tokens, or credentials.
- Keep all docs and examples sanitized: no real deal names, sponsor names, teammate names, internal service or repo names, email addresses, or allowlist contents.
- The MCP URL in `.mcp.json` is intentionally public and safe to expose; it is gated by sign-in on the server side.

## Layout

```
.claude-plugin/marketplace.json   marketplace manifest (marketplace name: "hfi")
plugins/
  hfi-deals/                       the deal pipeline plugin (.mcp.json, plugin.json, README)
  hfi-skills/                      scaffold for HFI-authored skills, not yet published
.claude/settings.json             commit attribution disabled
```

## Releasing an update

- Bump `version` in the plugin's `.claude-plugin/plugin.json`. Keep `version` in the plugin manifest only, not the marketplace entry, so there is one source of truth.
- A push to `main` ships to everyone who has the marketplace installed. There is no per-user approval gate, so review before pushing.
- This repo is deliberately separate from the deal pipeline service repo, so publishing a plugin update never triggers anything on the service side and vice versa.

## Adding a plugin or skill

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`.
2. Add what it provides: `skills/<name>/SKILL.md`, `commands/`, `agents/`, `hooks/hooks.json`, `.mcp.json` (one file may declare more than one MCP server).
3. List it in `.claude-plugin/marketplace.json`.
4. Commit and push.

Only put HFI-original skills here. Anthropic's prebuilt skill packs come from their own marketplaces; do not copy that content in.

## Git

This is a personal public repo (owner: mikedidierhfi). Normal commit flow on `main`. Attribution trailers are off via `.claude/settings.json`.
