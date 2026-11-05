# -*- coding: utf-8 -*-
import re
p = "/data/pado/make_ds_song.py"
src = open(p, encoding="utf-8").read()

new_fn = '''def build_line(row, chars_ts, f0_seq, line_start, line_end, wav_dur):
    """一行歌词 -> ds dict（时间基于整曲，严格限制在该行区间内）"""
    ph_seq, ph_dur, ph_num = [], [], []
    note_seq, note_dur, note_slur = [], [], []
    txt_tokens = []
    cursor = line_start
    limit = max(line_start + 0.1, line_end)

    def add_sil(g):
        if g <= 0.02:
            return
        ph_seq.append("SP"); ph_dur.append(round(g, 4)); ph_num.append(1)
        note_seq.append("rest"); note_dur.append(round(g, 3)); note_slur.append(0)
        txt_tokens.append("SP")

    for ch, (st, en) in zip(row, chars_ts):
        phs = hanzi_to_ph(ch)
        if not phs:
            continue
        # 严格 clamp：起点不早于游标，终点不越过行尾，且至少留 0.06s
        if cursor >= limit - 0.07:
            break
        st = min(max(st, cursor, line_start), limit - 0.07)
        en = min(max(en, st + 0.06), limit)
        if en - st < 0.05:
            en = min(limit, st + 0.05)
        add_sil(st - cursor)
        d = en - st
        if len(phs) == 2:
            durs = [round(d * 0.32, 4), round(d * 0.68, 4)]
        else:
            durs = [round(d / len(phs), 4) for _ in phs]
        durs[-1] = round(d - sum(durs[:-1]), 4)
        if durs[-1] < 0.01:
            durs[-1] = 0.01
        ph_seq.extend(phs); ph_dur.extend(durs); ph_num.append(len(phs))
        seg = f0_seq[int(st / F0_STEP): int(en / F0_STEP)]
        seg = [x for x in seg if x > 0]
        hz = float(np.median(seg)) if seg else 0.0
        note_seq.append(f0_to_note(hz)); note_dur.append(round(d, 3)); note_slur.append(0)
        txt_tokens.append(ch)
        cursor = en

    add_sil(limit - cursor)
    if not ph_seq:
        return None
    total = sum(ph_dur)
    if total <= 0.05:
        return None
    # 该区间的 F0 曲线
    i0 = int(line_start / F0_STEP)
    i1 = i0 + max(1, int(round(total / F0_STEP)))
    line_f0 = list(f0_seq[i0:i1])
    if len(line_f0) < i1 - i0:
        line_f0 += [0.0] * (i1 - i0 - len(line_f0))
    return {
        "offset": 0.0,
        "text": " ".join(txt_tokens),
        "ph_seq": " ".join(ph_seq),
        "ph_dur": " ".join(f"{x:.4f}" for x in ph_dur),
        "ph_num": " ".join(str(x) for x in ph_num),
        "note_seq": " ".join(note_seq),
        "note_dur": " ".join(f"{x:.3f}" for x in note_dur),
        "note_slur": " ".join(str(x) for x in note_slur),
        "f0_seq": " ".join(f"{x:.1f}" for x in line_f0),
        "f0_timestep": f"{F0_STEP}",
        "_span": total,
    }

'''

start = src.index("def build_line(")
end = src.index("def main(")
src = src[:start] + new_fn + src[end:]

# 切片改用 -t 时长，更可靠
src = src.replace(
'''        seg_start = max(0.0, line_start - 0.05)
        seg_end = min(dur, seg_start + span + 0.05)''',
'''        seg_start = max(0.0, line_start - 0.05)
        seg_len = min(dur - seg_start, span + 0.10)''')
src = src.replace(
'''        subprocess.run(["ffmpeg", "-y", "-ss", f"{seg_start:.3f}", "-to", f"{seg_end:.3f}",
                        "-i", args.wav, "-ar", "44100", "-ac", "1", seg_wav,
                        "-loglevel", "error"], check=False)''',
'''        subprocess.run(["ffmpeg", "-y", "-ss", f"{seg_start:.4f}", "-t", f"{seg_len:.4f}",
                        "-i", args.wav, "-ar", "44100", "-ac", "1", seg_wav,
                        "-loglevel", "error"], check=False)''')

# 整曲长度交给 ds 的 offset=0，ph_dur 从 line_start 开始，需保留行首静音
open(p, "w", encoding="utf-8").write(src)
print("已修补 build_line + 切片逻辑")
import ast
ast.parse(src)
print("语法 OK")
