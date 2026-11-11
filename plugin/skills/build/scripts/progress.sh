#!/bin/bash
# Prints a one-line status for a running build at intervals set by its estimated length. Run
# under the Monitor tool: each stdout line is an event. Reads project files and git, so it needs
# nothing from the builder and still reports when the builder has hung. Exits 0 once every
# project is in completed/. Safe to re-arm with the same arguments: state is kept per build.
# Every tick it also writes caddis-build.json in the git common dir for the build panel mod
# (plugin/hooks/panel.tsx) and leaves it there with "done": true at the end.
#
# Usage: progress.sh <start-epoch> <estimate-minutes> <project-path>...

if [ "$#" -lt 3 ]; then
  echo "usage: progress.sh <start-epoch> <estimate-minutes> <project-path>..." >&2
  exit 2
fi
start=$1
estimate=$(( $2 * 60 ))
shift 2

top=$(git rev-parse --show-toplevel 2>/dev/null)
git_dir=$(git rev-parse --absolute-git-dir 2>/dev/null) || { echo "progress.sh: not a git repo" >&2; exit 2; }
state="$git_dir/caddis-progress-$start"
# The common dir, so a build in a worktree lands where the panel looks: $.session.repo() names
# the main working tree's root for a worktree.
common_dir=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd) || common_dir=$git_dir
status_file="$common_dir/caddis-build.json"
tick=${CADDIS_PROGRESS_TICK:-15}
# Long enough to ride out a normal test run between edits, short enough to catch a hang.
stuck_after=1200

# The caddis/* worktrees, one path per line, refreshed each tick by scan.
worktrees() {
  git worktree list --porcelain 2>/dev/null | awk '
    /^worktree /{wt = substr($0, 10)}
    /^branch refs\/heads\/caddis\//{print wt}'
}

# The copy of a project to read. Builders in worktrees mark phases in their own copy when
# .caddis/ is tracked, so take a completed copy anywhere first, then the active copy with
# the most DONE markers, this checkout winning ties.
locate() {
  local name=$1 plan=$2 wt f n best="" best_n=-1
  for f in "$top/.caddis/projects/completed/$name"; do
    [ -f "$f" ] && { echo "$f"; return; }
  done
  while IFS= read -r wt; do
    [ -n "$wt" ] && [ -f "$wt/.caddis/projects/completed/$name" ] \
      && { echo "$wt/.caddis/projects/completed/$name"; return; }
  done <<< "$wts"
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    n=$(grep -c '^### Phase [0-9].* - DONE (' "$f")
    [ "$n" -gt "$best_n" ] && best=$f best_n=$n
  done < <(echo "$plan"; [ -n "$wts" ] && printf '%s\n' "$wts" | sed "s|\$|/.caddis/projects/active/$name|")
  echo "${best:-$plan}"
}

# Sets total, done, open and current from the project files.
scan() {
  wts=$(worktrees)
  total=0 done=0 open=0 current=""
  local plan name file phases marked
  for plan in "$@"; do
    name=$(basename "$plan")
    file=$(locate "$name" "$plan")
    phases=0 marked=0
    if [ -f "$file" ]; then
      phases=$(grep -c '^### Phase [0-9]' "$file")
      marked=$(grep -c '^### Phase [0-9].* - DONE (' "$file")
    fi
    case "$file" in
      *projects/active/*) ;;
      # A project gone from active/ is finished, whatever its phase markers say.
      *) [ "$phases" -gt 0 ] || phases=1
         total=$(( total + phases )) done=$(( done + phases ))
         continue ;;
    esac
    open=$(( open + 1 ))
    if [ "$phases" -eq 0 ]; then
      total=$(( total + 1 ))
    else
      total=$(( total + phases )) done=$(( done + marked ))
    fi
    if [ -z "$current" ]; then
      current=$(grep '^### Phase [0-9]' "$file" | grep -v ' - DONE (' | head -n 1 | sed 's/^### //')
      current="${name%.md}${current:+ $current}"
    fi
  done
}

# A JSON string: backslash and quote escaped, control characters (tabs included) dropped.
json_str() {
  local s
  s=$(printf '%s' "$1" | tr -d '\000-\037')
  s=${s//\\/\\\\}
  s=${s//\"/\\\"}
  printf '"%s"' "$s"
}

# The worktree on a project's builder branch, caddis/<name> with or without its project- prefix.
worktree_for() {
  git worktree list --porcelain 2>/dev/null | awk -v a="refs/heads/caddis/$1" \
    -v b="refs/heads/caddis/${1#project-}" '
    /^worktree /{wt = substr($0, 10)}
    $0 == "branch " a || $0 == "branch " b {print wt; exit}'
}

# What a project's builder has done since its last commit, read from its worktree, or from
# this checkout when no builder has a worktree: files changed outside .caddis/ and the newest
# edit or commit there since the build started. null for a project with nowhere to look yet.
activity_json() {
  local name=$1 dir changed=0 newest=0 stamp file
  dir=$(worktree_for "$name")
  [ -z "$dir" ] && [ -z "$wts" ] && dir=$top
  [ -n "$dir" ] && [ -d "$dir" ] || { echo null; return; }
  while IFS= read -r -d '' file; do
    case "$file" in
      # A nested repo or worktree (the agents' own under .claude/worktrees/) is not an edit.
      */) continue ;;
      .caddis/*) ;;
      *) changed=$(( changed + 1 )) ;;
    esac
    stamp=$(stat -c %Y "$dir/$file" 2>/dev/null || stat -f %m "$dir/$file" 2>/dev/null)
    [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  done < <({ git -C "$dir" diff --name-only -z HEAD 2>/dev/null || git -C "$dir" ls-files -m -z
             git -C "$dir" ls-files -o --exclude-standard -z; } 2>/dev/null | sort -zu)
  stamp=$(git -C "$dir" log -1 --format=%ct 2>/dev/null)
  [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  [ "$newest" -gt "$start" ] || newest=null
  printf '{"changed":%s,"last_edit":%s}' "$changed" "$newest"
}

# One project as a JSON object: its phases with done flags, the current phase and how many
# bullets sit under its Decisions During Build heading, and its builder's activity while open.
project_json() {
  local plan=$1 name file complete=false phases="" current="" line title isdone decisions=0 sep=""
  name=$(basename "$plan")
  file=$(locate "$name" "$plan")
  case "$file" in *projects/active/*) ;; *) complete=true ;; esac
  if [ -f "$file" ]; then
    while IFS= read -r line; do
      title=${line#\#\#\# }
      isdone=false
      case "$line" in *" - DONE ("*) isdone=true; title=${title% - DONE (*} ;; esac
      [ "$complete" = true ] && isdone=true
      [ "$isdone" = false ] && [ -z "$current" ] && current=$title
      phases="$phases$sep{\"name\":$(json_str "$title"),\"done\":$isdone}"
      sep=","
    done < <(grep '^### Phase [0-9]' "$file")
    decisions=$(awk '/^## /{on = ($0 ~ /^## Decisions During Build/)} on && /^[-*] /{n++} END{print n+0}' "$file")
  fi
  printf '{"name":%s,"complete":%s,"phases":[%s],"current":%s,"decisions":%s,"activity":%s}' \
    "$(json_str "${name%.md}")" "$complete" "$phases" \
    "$( [ -n "$current" ] && json_str "$current" || echo null )" "$decisions" \
    "$( [ "$complete" = true ] && echo null || activity_json "${name%.md}" )"
}

# Writes the status file atomically (a temp file, then mv), so the panel never reads half.
write_status() {
  local finished=$1 now idle quiet=false projects="" sep="" plan tmp
  now=$(date +%s)
  idle=$(( now - $(last_activity) ))
  [ "$idle" -ge "$stuck_after" ] && quiet=true
  for plan in "${plans[@]}"; do
    projects="$projects$sep$(project_json "$plan")"
    sep=","
  done
  tmp="$status_file.tmp.$$"
  printf '{"version":1,"start":%s,"estimate":%s,"elapsed":%s,"left":%s,"phases_done":%s,"phases_total":%s,"last_activity":%s,"idle":%s,"quiet":%s,"done":%s,"current":%s,"projects":[%s]}\n' \
    "$start" "$estimate" "$(( now - start ))" "${left:-null}" "$done" "$total" "$(( now - idle ))" \
    "$idle" "$quiet" "$finished" "$( [ -n "$current" ] && json_str "$current" || echo null )" \
    "$projects" > "$tmp" 2>/dev/null && mv -f "$tmp" "$status_file" 2>/dev/null
  rm -f "$tmp" 2>/dev/null
  return 0
}

fmt() {
  local minutes=$(( $1 / 60 ))
  if [ "$minutes" -lt 1 ]; then echo "<1m"
  elif [ "$minutes" -lt 60 ]; then echo "${minutes}m"
  else echo "$(( minutes / 60 ))h$(( minutes % 60 ))m"; fi
}

# Newest commit or uncommitted file change, never earlier than the start of the build.
# Builders in worktrees commit on caddis/<project> branches and edit files this checkout
# can't see, so those branches and the project files (kept here, often gitignored) count too.
last_activity() {
  local newest=$start stamp file plan
  for stamp in $(git log -1 --format=%ct 2>/dev/null) \
      $(git log -1 --format=%ct --branches='caddis/*' 2>/dev/null); do
    [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  done
  while IFS= read -r -d '' file; do
    stamp=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  done < <(git ls-files -m -o --exclude-standard -z 2>/dev/null)
  for plan in "${plans[@]}"; do
    file=$(locate "$(basename "$plan")" "$plan")
    [ -f "$file" ] || continue
    stamp=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  done
  echo "$newest"
}

plans=("$@")
scan "$@"
if [ -f "$state" ]; then
  read -r last base < "$state"
else
  last=$start base=$done
  echo "$last $base" > "$state"
fi

while :; do
  scan "$@"
  if [ "$open" -eq 0 ]; then
    rm -f "$state"
    left=0
    write_status true
    exit 0
  fi

  now=$(date +%s)
  elapsed=$(( now - start ))
  ran=$(( done - base ))
  # Measured pace once a phase has finished in this build, the estimate until then.
  if [ "$ran" -gt 0 ]; then
    left=$(( elapsed * (total - done) / ran ))
  else
    left=$(( estimate - elapsed ))
  fi
  if [ "$left" -gt 0 ]; then length=$(( elapsed + left )); else length=$elapsed; fi
  write_status false

  if [ "$length" -lt 300 ]; then interval=0
  elif [ "$length" -le 1800 ]; then interval=300
  elif [ "$length" -le 3600 ]; then interval=600
  elif [ "$length" -le 7200 ]; then interval=900
  else interval=1800; fi

  if [ "$interval" -gt 0 ] && [ $(( now - last )) -ge "$interval" ]; then
    if [ "$left" -ge 0 ]; then remaining="about $(fmt "$left") left"
    else remaining="past the $(fmt "$estimate") estimate"; fi
    idle=$(( now - $(last_activity) ))
    line="Caddis build: $done/$total phases, $(fmt "$elapsed") elapsed, $remaining. Current: $current. Last activity $(fmt "$idle") ago."
    [ "$idle" -ge "$stuck_after" ] && line="$line Possibly stuck."
    echo "$line"
    last=$now
    echo "$last $base" > "$state"
  fi
  sleep "$tick"
done
