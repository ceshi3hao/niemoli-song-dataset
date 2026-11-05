#!/bin/bash
source /data/niemoli-run-20261105/experiment/.venv/bin/activate
cd /data
mkdir -p /data/pado/ds /data/pado/asr
declare -A M=(
 ["01_99%"]="s01" ["02_帝都"]="s02" ["03_爱在西元前"]="s03" ["04_乱世书"]="s04"
 ["05_给我一首歌的时间"]="s05" ["06_原色"]="s06" ["07_折风渡夜"]="s07" ["08_求神呐"]="s08"
 ["09_盗橘令"]="s09" ["10_反方向的钟"]="s10" ["11_一格格"]="s11" ["12_月光"]="s12"
)
for name in "${!M[@]}"; do
  tag="${M[$name]}"
  wav=$(ls /data/pado/sep/${name}*Vocals*.wav 2>/dev/null | head -1)
  lrc="/data/pado/lyrics/${name}.lrc"
  if [ -z "$wav" ] || [ ! -f "$lrc" ]; then
    echo "SKIP $name (wav=$wav lrc=$lrc)"
    continue
  fi
  python /data/pado/make_ds_song.py --wav "$wav" --lrc "$lrc" --tag "$tag" \
    --out /data/pado/ds --asr "/data/pado/asr/${tag}.json" 2>&1 | grep -E "^LRC|^ASR|^DONE"
done
echo "BATCH_DONE"
