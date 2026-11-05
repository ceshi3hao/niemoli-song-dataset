#!/bin/bash
cd /data/pado
V=/data/niemoli-run-20261105/experiment/.venv
echo "[1] 转 wav"
for f in raw/*.m4a; do
  b=$(basename "$f" .m4a)
  [ -f "raw/${b}.wav" ] || ffmpeg -y -i "$f" -ar 44100 -ac 1 "raw/${b}.wav" -loglevel error
done
echo "[2] 等待前一批结束"
while pgrep -f "audio-separator" > /dev/null; do sleep 10; done
echo "[3] 批量分离"
export OMP_NUM_THREADS=32
$V/bin/audio-separator raw/*.wav \
  --model_filename UVR-MDX-NET-Inst_HQ_3.onnx \
  --single_stem Vocals --output_format WAV --output_dir /data/pado/sep \
  --mdx_batch_size 4
echo "SEP_ALL_DONE"
