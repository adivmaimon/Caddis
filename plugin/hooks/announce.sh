#!/bin/bash
# Show a one-line Caddis badge when a Caddis skill starts. Wired to two events:
#   UserPromptExpansion  you typed /caddis:<skill>
#   PreToolUse (Skill)   Claude chose the skill itself
# The systemMessage is shown to the user, not added to Claude's context. Silent for every
# other skill and when CADDIS_QUIET=1. Never blocks.

[ "${CADDIS_QUIET:-}" = "1" ] && exit 0
input=$(cat)
re='"(skill|command_name|command|prompt)"[[:space:]]*:[[:space:]]*"/?caddis:([A-Za-z0-9_-]+)'
if [[ $input =~ $re ]]; then
  printf '{"systemMessage": "●▮▮▪▪▫ caddis · %s"}\n' "${BASH_REMATCH[2]}"
fi
exit 0
