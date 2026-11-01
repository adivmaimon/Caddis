#!/bin/bash
# Prints a one-line status for a running build at intervals set by its estimated length. Run
# under the Monitor tool: each stdout line is an event. Reads plan files and git, so it needs
# nothing from the builder and still reports when the builder has hung. Exits 0 once every
# plan is in completed/. Safe to re-arm with the same arguments: state is kept per build.
#
# Usage: progress.sh <start-epoch> <estimate-minutes> <plan-path>...

if [ "$#" -lt 3 ]; then
  echo "usage: progress.sh <start-epoch> <estimate-minutes> <plan-path>..." >&2
  exit 2
fi
start=$1
estimate=$(( $2 * 60 ))
shift 2

git_dir=$(git rev-parse --absolute-git-dir 2>/dev/null) || { echo "progress.sh: not a git repo" >&2; exit 2; }
state="$git_dir/caddis-progress-$start"
tick=${CADDIS_PROGRESS_TICK:-15}
# Long enough to ride out a normal test run between edits, short enough to catch a hang.
stuck_after=1200

# Sets total, done, open and current from the plan files.
scan() {
  total=0 done=0 open=0 current=""
  local plan name file phases marked
  for plan in "$@"; do
    name=$(basename "$plan")
    file="$plan"
    [ -f "$file" ] || file=".caddis/projects/completed/$name"
    phases=0 marked=0
    if [ -f "$file" ]; then
      phases=$(grep -c '^### Phase [0-9]' "$file")
      marked=$(grep -c '^### Phase [0-9].* - DONE (' "$file")
    fi
    case "$file" in
      *projects/active/*) ;;
      # A plan gone from active/ is finished, whatever its phase markers say.
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

fmt() {
  local minutes=$(( $1 / 60 ))
  if [ "$minutes" -lt 1 ]; then echo "<1m"
  elif [ "$minutes" -lt 60 ]; then echo "${minutes}m"
  else echo "$(( minutes / 60 ))h$(( minutes % 60 ))m"; fi
}

# Newest commit or uncommitted file change, never earlier than the start of the build.
last_activity() {
  local newest=$start stamp file
  stamp=$(git log -1 --format=%ct 2>/dev/null)
  [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  while IFS= read -r -d '' file; do
    stamp=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    [ "${stamp:-0}" -gt "$newest" ] && newest=$stamp
  done < <(git ls-files -m -o --exclude-standard -z 2>/dev/null)
  echo "$newest"
}

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
