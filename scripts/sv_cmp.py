import os, glob, numpy as np, warnings
warnings.filterwarnings("ignore")
from resemblyzer import VoiceEncoder, preprocess_wav

enc = VoiceEncoder("cpu")
print("encoder ready")

def emb(fp, max_sec=40):
    w = preprocess_wav(fp)
    if len(w) > max_sec * 16000:
        w = w[: max_sec * 16000]
    return enc.embed_utterance(w)

# 聂莫黎对白（同一说话人，作为音色锚点）
spk = sorted(glob.glob("/data/gsv_data/nm2/*.wav"))[:8]
spk_embs = [emb(f) for f in spk]
spk_mean = np.mean(spk_embs, axis=0)

print("=== 对白内部一致性（同一人不同句）===")
for i in range(min(4, len(spk_embs))):
    s = float(np.dot(spk_embs[i], spk_mean) / (np.linalg.norm(spk_embs[i]) * np.linalg.norm(spk_mean)))
    print(f"  {os.path.basename(spk[i])}: {s:.3f}")

print()
print("=== 歌人声 vs 聂莫黎对白 ===")
for f in glob.glob("/data/pado/sep/*Vocals*.wav"):
    e = emb(f)
    s = float(np.dot(e, spk_mean) / (np.linalg.norm(e) * np.linalg.norm(spk_mean)))
    print(f"  {os.path.basename(f)[:32]:34s} 相似度 {s:.3f}")

# 歌与歌之间
print()
print("=== 歌与歌之间 ===")
fs = glob.glob("/data/pado/sep/*Vocals*.wav")
es = [emb(f) for f in fs]
for i in range(len(es)):
    for j in range(i+1, len(es)):
        s = float(np.dot(es[i], es[j]) / (np.linalg.norm(es[i]) * np.linalg.norm(es[j])))
        print(f"  {os.path.basename(fs[i])[:18]} vs {os.path.basename(fs[j])[:18]}: {s:.3f}")
