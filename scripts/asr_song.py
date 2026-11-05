import os, json, re, difflib
os.environ["MODELSCOPE_CACHE"]="/data/ms_cache"
from funasr import AutoModel

WAV = "/data/pado/sep/01_99%_(Vocals)_UVR-MDX-NET-Inst_HQ_3.wav"
m = AutoModel(model="paraformer-zh", vad_model="fsmn-vad", punc_model="ct-punc",
              device="cuda", disable_update=True)
r = m.generate(input=WAV, sentence_timestamp=True, batch_size_s=200)[0]
print("识别文本:", r.get("text","")[:300])
print("片段数:", len(r.get("sentence_info",[])))
for s in r.get("sentence_info",[])[:5]:
    print(f"  {s['start']/1000:6.2f}-{s['end']/1000:6.2f}  {s['text']}")
json.dump(r, open("/data/pado/asr_01.json","w"), ensure_ascii=False)

# 和 LRC 对比
lrc=[]
for l in open("/data/pado/lyrics_01.txt", encoding="utf-8"):
    t=l.strip()
    if t: lrc.append(t)
KEEP=re.compile(r"[^\u4e00-\u9fff]")
def n(s): return KEEP.sub("", s)
asr = n(r.get("text",""))
print()
print(f"ASR {len(asr)} 字  vs LRC {sum(len(x) for x in lrc)} 字")
print("整体相似度:", round(difflib.SequenceMatcher(None, asr, n("".join(lrc))).ratio(), 3))
