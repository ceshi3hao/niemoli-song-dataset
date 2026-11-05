#!/bin/bash
cd /data/pado
V=/data/niemoli-run-20261105/experiment/.venv
for f in raw/01_99%.m4a raw/12_月光.m4a; do
  b=$(basename "$f" .m4a)
  ffmpeg -y -i "$f" -ar 44100 -ac 1 "raw/${b}.wav" -loglevel error
done
export OMP_NUM_THREADS=32
$V/bin/audio-separator "raw/01_99%.wav" "raw/12_月光.wav" \
  --model_filename UVR-MDX-NET-Inst_HQ_3.onnx \
  --single_stem Vocals --output_format WAV --output_dir /data/pado/sep \
  --mdx_batch_size 4
echo "SEP2_DONE"
