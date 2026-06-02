# HFI skills

This is the home for HFI-authored skills. It is intentionally empty for now.

To add a skill, create a folder here with a `SKILL.md` file:

```
plugins/hfi-skills/skills/
  term-sheet/
    SKILL.md
  ic-memo/
    SKILL.md
```

A `SKILL.md` starts with YAML frontmatter (`name`, `description`) followed by the instructions. The `description` is what Claude matches against to decide when to trigger the skill, so make it specific about when to use it and when not to.

When at least one real skill is here, publish the plugin by adding it to the root `.claude-plugin/marketplace.json`:

```json
{
  "name": "hfi-skills",
  "source": "./plugins/hfi-skills",
  "description": "HFI-authored skills: term sheets, IC memos, deal workflows."
}
```

Bump `version` in this plugin's `.claude-plugin/plugin.json` each time you want installed copies to update.

Note: only put HFI-original skills here. Anthropic's prebuilt skill packs (investment-banking, financial-analysis, private-equity, and so on) come from their own marketplaces. Have teammates add those marketplaces directly rather than copying that content into this repo.
