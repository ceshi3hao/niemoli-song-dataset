#!/bin/bash
cd /data/pado
V=/data/niemoli-run-20261105/experiment/.venv
for k in 07 08 09 10 11; do
  [ -f "raw/s${k}.wav" ] || ffmpeg -y -i "raw/s${k}.m4a" -ar 44100 -ac 1 "raw/s${k}.wav" -loglevel error
done
export OMP_NUM_THREADS=32
$V/bin/audio-separator raw/s07.wav raw/s08.wav raw/s09.wav raw/s10.wav raw/s11.wav \
  --model_filename UVR-MDX-NET-Inst_HQ_3.onnx --single_stem Vocals \
  --output_format WAV --output_dir /data/pado/sep --mdx_batch_size 4
echo "SEP_REST_DONE"
