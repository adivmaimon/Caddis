#!/bin/bash
# Load the repo's rules into context: .caddis/rulebook.md (without its Retired section) and
# the Invariants section of .caddis/caddis.md. Wired to two events:
#   SessionStart   every source (startup, resume, clear, compact); plain stdout is context
#   SubagentStart  every subagent; context must go in hookSpecificOutput.additionalContext
# Silent when the repo has neither. Never fails the session.

mode="${1:-session}"
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

rules=""
if [ -f .caddis/rulebook.md ]; then
  rules=$(awk '/^## Retired/ {exit} /^[[:space:]]*<!--.*-->[[:space:]]*$/ {next} {print}' .caddis/rulebook.md)
fi
inv=""
if [ -f .caddis/caddis.md ]; then
  inv=$(awk '/^## Invariants/ {on=1; next} on && /^## / {exit}
    on && /^[[:space:]]*<!--/ {c=1} on && !c && NF {print} c && /-->/ {c=0}' .caddis/caddis.md)
fi
[ -n "$rules$inv" ] || exit 0

text="Rules agreed for this repo. Follow them in everything you write. When the owner gives a new rule, corrects you, or says a rule no longer holds, update .caddis/rulebook.md in the same turn (the caddis rulebook skill) before carrying on."
[ -n "$rules" ] && text="$text"$'\n\n'"$rules"
[ -n "$inv" ] && text="$text"$'\n\n'"## Invariants (.caddis/caddis.md)"$'\n\n'"$inv"

if [ "$mode" = "subagent" ]; then
  esc=$(printf '%s' "$text" | awk 'BEGIN {ORS=""} {gsub(/\\/, "\\\\"); gsub(/"/, "\\\""); gsub(/\t/, "\\t"); gsub(/\r/, ""); if (NR > 1) print "\\n"; print}')
  printf '{"hookSpecificOutput": {"hookEventName": "SubagentStart", "additionalContext": "%s"}}\n' "$esc"
else
  printf '%s\n' "$text"
fi
exit 0
