#!/usr/bin/env bash
# Status line: shows model, context and weekly budget, and stores the weekly
# value in .claude/budget/weekly.json for budget.sh (FAHRPLAN_PHASE_2 rhythm).
input=$(cat)
dir="$(cd "$(dirname "$0")" && pwd)/budget"
week=$(jq -r '.rate_limits.seven_day.used_percentage // empty' <<<"$input")
reset=$(jq -r '.rate_limits.seven_day.resets_at // empty' <<<"$input")
if [ -n "$week" ]; then
  mkdir -p "$dir"
  printf '{"used_percentage": %s, "resets_at": %s, "seen_at": %s}\n' \
    "$week" "${reset:-null}" "$(date +%s)" >"$dir/weekly.json.tmp"
  mv "$dir/weekly.json.tmp" "$dir/weekly.json"
fi
model=$(jq -r '.model.display_name // "?"' <<<"$input")
ctx=$(jq -r '.context_window.used_percentage // 0' <<<"$input" | cut -d. -f1)
echo "[$model] Kontext ${ctx}% · Woche ${week:-–}%"
