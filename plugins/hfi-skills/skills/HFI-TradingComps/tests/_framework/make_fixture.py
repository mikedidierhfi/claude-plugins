#!/usr/bin/env python3
"""
make_fixture.py — Build a small, frozen test fixture from a full SEC companyfacts JSON.

The full companyfacts file is many MB; a fixture only needs the handful of concepts the skill
uses (per assets/xbrl_tags.json). This trims to those concepts so tests are deterministic,
offline, and the package stays lean.

Usage:
  python make_fixture.py <companyfacts_in.json> <fixture_out.json>
"""
import json, os, sys

ASSETS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
with open(os.path.join(ASSETS, "xbrl_tags.json"), "r", encoding="utf-8") as f:
    TAGS = json.load(f)

NEEDED = set()
for key, spec in TAGS.items():
    if isinstance(spec, dict) and "tags" in spec:
        for t in spec["tags"]:
            NEEDED.add((t["taxonomy"], t["tag"]))


def trim(facts):
    out = {"cik": facts.get("cik"), "entityName": facts.get("entityName"), "facts": {}}
    for tax, concepts in facts.get("facts", {}).items():
        for tag, node in concepts.items():
            if (tax, tag) in NEEDED:
                out["facts"].setdefault(tax, {})[tag] = node
    return out


def main(argv=None):
    argv = argv or sys.argv[1:]
    src, dst = argv[0], argv[1]
    with open(src, "r", encoding="utf-8") as f:
        facts = json.load(f)
    trimmed = trim(facts)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(trimmed, f)
    n = sum(len(v) for v in trimmed["facts"].values())
    print(f"Wrote {dst}: {n} concepts kept (of needed {len(NEEDED)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
