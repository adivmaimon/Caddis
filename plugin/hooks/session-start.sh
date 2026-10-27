#!/bin/bash
# SessionStart: if this repo uses Caddis and its codebase map is out of date, say so.
# Plain stdout from a SessionStart hook goes to Claude as context. Silent when the map is
# fresh or the repo has no Caddis map. Never fails the session.

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
map=".caddis/map/STRUCTURE.md"
[ -f "$map" ] || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# The first line of STRUCTURE.md is <!-- caddis-map commit: abc1234 -->
stamp=""
re='caddis-map commit: ([0-9a-f]+)'
while IFS= read -r line; do
  if [[ $line =~ $re ]]; then stamp="${BASH_REMATCH[1]}"; break; fi
done < "$map"
[ -n "$stamp" ] || exit 0
git cat-file -e "$stamp^{commit}" 2>/dev/null || exit 0

src='\.(js|jsx|mjs|cjs|ts|tsx|mts|cts|vue|svelte|astro|py|go|rs|php|rb|java|kt|kts|scala|swift|cs|dart|c|h|cc|cpp|cxx|hpp|hh|m|mm|css|scss|sass|less)$'
changed=$( { git diff --name-only "$stamp" -- 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } \
  | grep -E "$src" | grep -v -E '(^|/)(\.caddis|node_modules|vendor)/' | sort -u | grep -c . )
[ "${changed:-0}" -gt 0 ] || exit 0
behind=$(git rev-list --count "$stamp..HEAD" -- . ':(exclude).caddis' 2>/dev/null || echo 0)

echo "Caddis map: STRUCTURE.md is ${behind} commit(s) behind, and ${changed} source file(s) have changed since. Refresh it with the caddis map skill before relying on it."
exit 0
