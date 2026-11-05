import glob, os, re, shutil

def num_of(p):
    b = os.path.basename(p)
    m = re.match(r"(\d{2})_", b)
    return m.group(1) if m else None

n = 0
for f in glob.glob("/data/pado/lyrics/*.lrc"):
    k = num_of(f)
    if not k: continue
    dst = f"/data/pado/lyrics/s{k}.lrc"
    if f != dst:
        shutil.move(f, dst); n += 1

for f in glob.glob("/data/pado/raw/*"):
    k = num_of(f)
    if not k: continue
    ext = os.path.splitext(f)[1]
    dst = f"/data/pado/raw/s{k}{ext}"
    if f != dst:
        shutil.move(f, dst); n += 1

for f in glob.glob("/data/pado/sep/*Vocals*.wav"):
    k = num_of(f)
    if not k: continue
    dst = f"/data/pado/sep/s{k}_vocals.wav"
    if f != dst:
        shutil.move(f, dst); n += 1

print(f"重命名 {n} 个")
print("lyrics:", sorted(os.path.basename(x) for x in glob.glob("/data/pado/lyrics/*.lrc")))
print("sep   :", sorted(os.path.basename(x) for x in glob.glob("/data/pado/sep/*.wav")))
print("raw   :", sorted(os.path.basename(x) for x in glob.glob("/data/pado/raw/*.m4a")))
