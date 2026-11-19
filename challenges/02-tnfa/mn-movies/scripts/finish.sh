#!/usr/bin/env bash
# Post-process a raw Molecular Nodes render: fades + captions, H264 for the web.
# usage: finish.sh <raw.mp4> <design> <ns> <out.mp4>
set -euo pipefail
raw=$1; design=$2; ns=$3; out=$4
font=$HOME/.fonts/JetBrainsMono-Regular.ttf
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$raw")
fade_out=$(python3 -c "print(round(max(0.0, float('$dur') - 0.5), 2))")
line1="$design  ·  $ns ns MD at 300 K  ·  binder (pink) vs TNF-α (blue)  ·  interface (amber)"
line2="physics test of the predicted pose — not a binding assay"
ffmpeg -y -v error -i "$raw" -vf "\
drawbox=x=0:y=ih-124:w=iw:h=124:color=0x0b0f14@0.62:t=fill,\
drawtext=fontfile=$font:text='$line1':fontcolor=0xcdd6e4:fontsize=30:x=48:y=h-88,\
drawtext=fontfile=$font:text='$line2':fontcolor=0x8b93a7:fontsize=26:x=48:y=h-52,\
fade=t=in:st=0:d=0.5,fade=t=out:st=$fade_out:d=0.5" \
  -c:v libx264 -crf 17 -preset slow -pix_fmt yuv420p -movflags +faststart "$out"
echo "wrote $out"
