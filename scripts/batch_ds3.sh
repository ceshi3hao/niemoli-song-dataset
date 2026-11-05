#!/bin/bash
source /data/niemoli-run-20261105/experiment/.venv/bin/activate
cd /data
for i in 07 08 09 10 11; do
  wav=/data/pado/sep/s${i}_vocals.wav
  [ -f "$wav" ] || { echo "SKIP s$i 无音频"; continue; }
  python /data/pado/make_ds_song.py --wav "$wav" --lrc /data/pado/lyrics/s${i}.lrc --tag s${i} --out /data/pado/ds --asr /data/pado/asr/s${i}.json 2>&1 | grep -E '^LRC|^ASR|^DONE|Error|Traceback'
done
echo BATCH3_DONE
