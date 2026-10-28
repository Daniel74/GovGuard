#!/usr/bin/env bash
# Measures the weekly budget of one FAHRPLAN_PHASE_2 step from the value the
# status line stores (.claude/statusline.sh).
#   budget.sh start <step>                      remember the weekly value
#   budget.sh end <step> "<estimate>" [<issue>...] row in SCHAETZUNG.md, issue comments
#   budget.sh set <percent>                     fallback: value read from /usage
# BUDGET_DIR, BUDGET_LOG and BUDGET_DRY_RUN=1 (no gh call) exist for tests.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
dir="${BUDGET_DIR:-$root/.claude/budget}"
log="${BUDGET_LOG:-$root/docs/SCHAETZUNG.md}"
stale_after=1800

current() {
  [ -f "$dir/weekly.json" ] || { echo "Kein Wochenwert: Die Statuszeile hat noch nichts geschrieben. Wert aus /usage mit 'budget.sh set <Prozent>' eintragen." >&2; exit 1; }
  local age=$(( $(date +%s) - $(jq -r .seen_at "$dir/weekly.json") ))
  [ "$age" -le "$stale_after" ] || echo "Warnung: Wochenwert ist $((age / 60)) min alt." >&2
  cat "$dir/weekly.json"
}

set_manual() {
  mkdir -p "$dir"
  printf '{"used_percentage": %s, "resets_at": null, "seen_at": %s}\n' "$1" "$(date +%s)" >"$dir/weekly.json"
}

start() {
  current >"$dir/$1.start"
  echo "Budget $1 Start: $(jq -r .used_percentage "$dir/$1.start") % Weekly"
}

measured() {
  local before="$1" after="$2"
  if [ "$(jq -r .resets_at "$before")" != "$(jq -r .resets_at <<<"$after")" ]; then
    echo "nicht messbar (Wochenlimit zwischendurch zurückgesetzt)"
  else
    jq -rn --slurpfile a "$before" --argjson b "$after" \
      '(($b.used_percentage - $a[0].used_percentage) * 10 | round) / 10 | "\(.) % Weekly"' | tr . ,
  fi
}

log_row() {
  # Inserts the row after the last table row of section "## 3."
  local row="| $1 | $(date +%d.%m.%Y) | $2 | $3 | $4 |"
  awk -v row="$row" '
    /^## 3\./ { in3 = 1 }
    in3 && /^\|/ { last = NR }
    { lines[NR] = $0 }
    END { for (i = 1; i <= NR; i++) { print lines[i]; if (i == last) print row } }
  ' "$log" >"$log.tmp" && mv "$log.tmp" "$log"
}

end() {
  local step="$1" estimate="$2"
  shift 2
  [ -f "$dir/$step.start" ] || { echo "Kein Startwert für $step: erst 'budget.sh start $step'." >&2; exit 1; }
  local after ist refs=""
  after="$(current)"
  ist="$(measured "$dir/$step.start" "$after")"
  for issue in "$@"; do refs="${refs:+$refs, }#$issue"; done
  log_row "$step" "$refs" "$estimate" "$ist"
  local body="Budget $step: geschätzt $estimate, Ist $ist"
  if [ "${BUDGET_DRY_RUN:-0}" != 1 ]; then
    for issue in "$@"; do gh issue comment "$issue" --body "$body" >/dev/null; done
  fi
  rm "$dir/$step.start"
  echo "$body"
}

case "${1:-}" in
  start) start "$2" ;;
  set) set_manual "$2" ;;
  end) shift; end "$@" ;;
  *) echo "Aufruf: budget.sh start <Schritt> | set <Prozent> | end <Schritt> \"<Schätzung>\" [<Issue> ...]" >&2; exit 2 ;;
esac
