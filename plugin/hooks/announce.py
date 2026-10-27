"""Show a one-line Caddis badge when a Caddis skill starts.

Two ways a skill starts, two hook events:
  UserPromptExpansion  you typed /caddis:<skill>
  PreToolUse (Skill)   Claude chose the skill itself, e.g. from "create a task to..."

Prints a systemMessage, which Claude Code shows to the user and does not add to Claude's
context. Silent for everything else, and when CADDIS_QUIET=1. Never blocks.
"""
import json
import os
import re
import sys

BADGE = "●▮▮▪▪▫ caddis · {}"  # the case: pebbles getting smaller away from the head


def caddis_skill(event):
    if event.get("hook_event_name") == "PreToolUse" or event.get("tool_name"):
        if event.get("tool_name") != "Skill":
            return None
        values = [str((event.get("tool_input") or {}).get("skill", ""))]
    else:
        # Field names differ across versions; look at every string the event carries.
        values = [str(v) for v in event.values() if isinstance(v, str)]
    for v in values:
        m = re.match(r"\s*/?caddis:([\w-]+)", v)
        if m:
            return m.group(1)
    return None


try:
    if os.environ.get("CADDIS_QUIET") != "1":
        name = caddis_skill(json.load(sys.stdin))
        if name:
            print(json.dumps({"systemMessage": BADGE.format(name)}))
except Exception:
    pass
sys.exit(0)
