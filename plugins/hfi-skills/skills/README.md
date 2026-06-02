# HFI skills

HFI-authored skills live here, one folder per skill with a `SKILL.md` inside:

```
plugins/hfi-skills/skills/
  deal-brief/
    SKILL.md
```

A `SKILL.md` is YAML frontmatter (`name`, `description`) followed by instructions. The `description` is what Claude matches on to decide when to run the skill, so be specific about when to use it and when not to.

To add a skill: create the folder and `SKILL.md`, bump `version` in `../.claude-plugin/plugin.json`, validate with `claude plugin validate ./plugins/hfi-skills`, commit, and push. Installed copies update on the next sync.

Many of these skills call the deal pipeline, so they work best when the user also has the `hfi-deals` plugin installed and is signed in.

Only HFI-original skills go here. Anthropic's prebuilt skill packs come from their own marketplaces; do not copy that content in.
