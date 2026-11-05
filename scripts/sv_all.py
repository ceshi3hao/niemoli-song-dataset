import os, glob, numpy as np, warnings
warnings.filterwarnings("ignore")
from resemblyzer import VoiceEncoder, preprocess_wav

enc = VoiceEncoder("cpu")
def emb(fp, max_sec=60):
    w = preprocess_wav(fp)
    if len(w) > max_sec * 16000:
        w = w[: max_sec * 16000]
    return enc.embed_utterance(w)

files = sorted(glob.glob("/data/pado/sep/*_vocals.wav"))
names = [os.path.basename(f)[:3] for f in files]
es = [emb(f) for f in files]
M = np.array(es)
M = M / np.linalg.norm(M, axis=1, keepdims=True)
S = M @ M.T

print("     " + " ".join(f"{n:>6s}" for n in names))
for i, n in enumerate(names):
    print(f"{n}  " + " ".join(f"{S[i,j]:6.3f}" for j in range(len(names))))
print()
off = [S[i, j] for i in range(len(names)) for j in range(i+1, len(names))]
print(f"两两相似度: 均值 {np.mean(off):.3f}  最低 {np.min(off):.3f}  最高 {np.max(off):.3f}")

# 对白锚点
spk = sorted(glob.glob("/data/gsv_data/nm2/*.wav"))[:6]
sp = np.mean([emb(f) for f in spk], axis=0)
sp = sp / np.linalg.norm(sp)
print()
print("与聂莫黎对白:")
for i, n in enumerate(names):
    print(f"  {n}: {float(S[i] @ sp):.3f}")
