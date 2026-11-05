import os
os.environ["MODELSCOPE_CACHE"] = "/data/ms_cache"
from funasr import AutoModel

m = AutoModel(model="cam++", model_revision="v2.0.4", disable_update=True, device="cuda")
print("cam++ 加载 OK")
a = "/data/gsv_data/nm2/n2_0004.wav"
b = "/data/gsv_data/nm2/n2_0000.wav"
r = m.generate(input=[a, b])
print("两条对白相似度:", r)
