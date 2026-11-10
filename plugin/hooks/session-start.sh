#!/bin/bash
# SessionStart: if this repo uses Caddis, say when its config predates the installed Caddis
# and when its codebase map is out of date. Plain stdout from a SessionStart hook goes to
# Claude as context. Silent when both are current or the repo doesn't use Caddis. Never
# fails the session.

cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0

# An update can add settings. caddis.md's first line records the version it was last brought
# up to date with, <!-- caddis-config: 0.6.0 -->; no marker means older than 0.6.0.
config=".caddis/caddis.md"
manifest="${CLAUDE_PLUGIN_ROOT:-}/.claude-plugin/plugin.json"
if [ -f "$config" ] && [ -f "$manifest" ]; then
  plugin=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([0-9.]*\)".*/\1/p' "$manifest" | head -n 1)
  seen=$(sed -n '1s/.*caddis-config: \([0-9.]*\).*/\1/p' "$config")
  seen=${seen:-0}
  newest=$(printf '%s\n%s\n' "$seen" "$plugin" | sort -t. -k1,1n -k2,2n -k3,3n | tail -n 1)
  if [ -n "$plugin" ] && [ "$seen" != "$plugin" ] && [ "$newest" = "$plugin" ]; then
    echo "Caddis was updated to $plugin. This repo's config and team rules are unchanged. Run /caddis:config to see any new settings."
  fi
fi

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

# The map is usually committed together with the work it describes, so a later commit that
# touched STRUCTURE.md is the real baseline: whoever committed it saw those changes.
last=$(git log -1 --format=%h -- "$map" 2>/dev/null)
if [ -n "$last" ] && git merge-base --is-ancestor "$stamp" "$last" 2>/dev/null; then stamp="$last"; fi

src='\.(js|jsx|mjs|cjs|ts|tsx|mts|cts|vue|svelte|astro|py|go|rs|php|rb|java|kt|kts|scala|swift|cs|dart|c|h|cc|cpp|cxx|hpp|hh|m|mm|css|scss|sass|less)$'
changed=$( { git diff --name-only "$stamp" -- 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null; } \
  | grep -E "$src" | grep -v -E '(^|/)(\.caddis|node_modules|vendor)/' | sort -u | grep -c . )
[ "${changed:-0}" -gt 0 ] || exit 0
behind=$(git rev-list --count "$stamp..HEAD" -- . ':(exclude).caddis' 2>/dev/null || echo 0)

echo "Caddis map: STRUCTURE.md is ${behind} commit(s) behind, and ${changed} source file(s) have changed since. Refresh it with the caddis map skill before relying on it."
exit 0
