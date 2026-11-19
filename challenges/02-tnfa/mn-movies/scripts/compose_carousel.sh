#!/usr/bin/env bash
# Composite the binder alpha pass over the full render.
#
# The full pass keeps the reference look (opaque grey surface); the binder
# pass draws the current design with the target invisible to the camera (but
# still casting its pocket light/shadow), so binders tucked into a groove
# stay visible.  Overlaying the second pass on the first leaves the surface
# and every protruding binder exactly as rendered.
#
# usage: compose_carousel.sh <full.mp4> <binder_dir> <out.mp4>
set -euo pipefail
full=$1; bdir=$2; out=$3
ffmpeg -y -v error -i "$full" -framerate 24 -i "$bdir/binder_%04d.png" \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto" \
  -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -movflags +faststart "$out"
echo "wrote $out"
