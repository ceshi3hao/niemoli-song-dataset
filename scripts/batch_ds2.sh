#!/bin/bash
source /data/niemoli-run-20261105/experiment/.venv/bin/activate
cd /data
mkdir -p /data/pado/ds /data/pado/asr
for wav in /data/pado/sep/s*_vocals.wav; do
  b=$(basename "$wav")
  tag=${b%%_vocals.wav}
  lrc="/data/pado/lyrics/${tag}.lrc"
  [ -f "$lrc" ] || { echo "SKIP $tag no-lrc"; continue; }
  [ -d "/data/pado/ds_done/$tag" ] && { echo "SKIP $tag done"; continue; }
  python /data/pado/make_ds_song.py --wav "$wav" --lrc "$lrc" --tag "$tag" \
    --out /data/pado/ds --asr "/data/pado/asr/${tag}.json" 2>&1 | grep -E "^LRC|^ASR|^DONE|Error|Traceback"
done
echo "BATCH2_DONE"
