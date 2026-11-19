#!/usr/bin/env bash
# Contact sheet: one frame per second, 3x2 tile, for the repo QA record.
# usage: qa_sheet.sh <clip.mp4> <out.png>
set -euo pipefail
clip=$1; out=$2
ffmpeg -y -v error -i "$clip" \
  -vf "select='isnan(prev_selected_t)+gte(t-prev_selected_t,1)',scale=960:540,tile=3x2" \
  -frames:v 1 "$out"
echo "wrote $out"
