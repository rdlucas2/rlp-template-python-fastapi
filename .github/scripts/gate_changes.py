"""Gate changes of a pull request to this template repo (rdlucas2/rlp#88).

This repo is a Copier template, not an rlp project, so it doesn't run the golden
pipeline whose policy stage feeds `rlp pipeline gate-review`. This script stands
in for that stage. It writes a results.json whose policy stage lists, under
data.gate_changes:

- every warning of the rlp.agent rules (`rlp policy check -n rlp.agent`) on this
  repo: protected gate files, suppressions and so on, judged as rlp judges them;
- for an agent-authored change (the agent:authored label, or an author in rlp's
  agent_authors), every other changed file that .github/CODEOWNERS assigns an
  owner. Most of the template's gates are .jinja sources under template/
  (template/tests/, template/rlp.yaml.jinja), whose names the rlp.agent rules
  don't recognise.

`rlp pipeline gate-review --results <file>` then holds the PR until a human who
is not its author approves the head commit. The change (author, labels, files
since the baseline) is read the way `rlp policy check` reads it: from the
pull_request event at $GITHUB_EVENT_PATH and the commit in $RLP_BASELINE.

Usage: python .github/scripts/gate_changes.py --results PATH [--root DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from rlp_cli import baseline, change, gate_review, policy

AGENT_LABEL = "agent:authored"
VERB = {"A": "adds", "D": "deletes"}


def codeowners(root: Path) -> list[tuple[re.Pattern, list[str]]]:
    """The rules of .github/CODEOWNERS as (regex, owners), in file order."""
    path = root / ".github" / "CODEOWNERS"
    if not path.is_file():
        raise SystemExit(f"error: {path} not found")
    rules = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, *owners = line.split()
            rules.append((pattern_regex(pattern), owners))
    return rules


def pattern_regex(pattern: str) -> re.Pattern:
    """A CODEOWNERS (gitignore-style) pattern as a regex over repo-relative paths."""
    directory = pattern.endswith("/")
    body = pattern.strip("/")
    anchored = pattern.startswith("/") or "/" in body
    parts, i = [], 0
    while i < len(body):
        if body.startswith("**/", i):
            parts.append("(?:.*/)?")
            i += 3
        elif body.startswith("**", i):
            parts.append(".*")
            i += 2
        elif body[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif body[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(body[i]))
            i += 1
    prefix = "" if anchored else "(?:.*/)?"
    suffix = "/.*" if directory else "(?:/.*)?"
    return re.compile(f"^{prefix}{''.join(parts)}{suffix}$")


def owners_of(path: str, rules: list[tuple[re.Pattern, list[str]]]) -> list[str]:
    """The owners of path: the last matching rule wins, as on GitHub."""
    found: list[str] = []
    for regex, owners in rules:
        if regex.match(path):
            found = owners
    return found


def agent_authored(author: str, labels: list[str], agents: list[str]) -> bool:
    return AGENT_LABEL in labels or author.lower() in {a.lower() for a in agents}


def gate_changes(root: Path) -> list[dict]:
    doc = change.build(root)
    found = [w.as_dict() for w in policy.check(root, ("rlp.agent",), doc).warnings]
    facts = doc[change.KEY]
    if not agent_authored(facts["author"], facts["labels"], gate_review.agent_authors()):
        return found
    flagged = {g["file"] for g in found}
    rules = codeowners(root)
    for f in facts["files"]:
        owners = owners_of(f["path"], rules)
        if f["path"] in flagged or not owners:
            continue
        verb = VERB.get(f["status"], "edits")
        found.append({
            "rule": "CODEOWNERS",
            "file": f["path"],
            "field": "(file)",
            "message": (
                f"[CODEOWNERS] {f['path']} (file): an agent-authored change {verb} a gate file of this template. "
                f"Fix: {' '.join(owners)} reviews the change"
            ),
            "namespace": "codeowners",
        })
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=Path("."), help="Repo root (default: current directory)")
    parser.add_argument("--results", type=Path, required=True, help="results.json to write")
    args = parser.parse_args(argv)
    try:
        changes = gate_changes(args.root)
    except (policy.PolicyError, change.ChangeError, baseline.BaselineError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    detail = f"{len(changes)} gate change(s) needing review" if changes else "no gate changes"
    stage = {"stage": "policy", "status": "passed", "detail": detail, "data": {"gate_changes": changes}}
    args.results.parent.mkdir(parents=True, exist_ok=True)
    args.results.write_text(json.dumps([stage], indent=2) + "\n", encoding="utf-8")
    print(detail)
    for g in changes:
        print(f"- {g['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
