# -*- coding: utf-8 -*-
"""歌曲 -> DiffSinger .ds 标注：LRC 行切分 + ASR 字级时间 + 鲁棒 F0"""
import os, sys, json, re, math, difflib, argparse, subprocess
import numpy as np
import parselmouth
from pypinyin import pinyin, Style

DICT_PATH = "/data/DiffSinger/dictionaries/niemoli.txt"
F0_STEP = 0.005

def load_dict():
    d = {}
    for line in open(DICT_PATH, encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) == 2:
            d[p[0]] = p[1]
    return d
PH_DICT = load_dict()

PUNCT = re.compile(r"[^\u4e00-\u9fff]")

def hanzi_to_ph(ch):
    py = pinyin(ch, style=Style.NORMAL, errors="ignore")
    if not py or not py[0]:
        return None
    s = py[0][0].replace("ü", "v")
    return PH_DICT[s].split() if s in PH_DICT else None

def f0_to_note(hz):
    if hz <= 0:
        return "rest"
    midi = int(round(69 + 12 * math.log2(hz / 440.0)))
    names = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
    return f"{names[midi % 12]}{midi // 12 - 1}"

def parse_lrc(path):
    rows = []
    for l in open(path, encoding="utf-8"):
        m = re.match(r"\[(\d+):(\d+)[.:](\d+)\](.*)", l.strip())
        if not m:
            continue
        t = int(m.group(1)) * 60 + int(m.group(2)) + int(m.group(3)) / 100.0
        txt = m.group(4).strip()
        if not txt or "Vemus" in txt or "未音" in txt:
            continue
        txt = PUNCT.sub("", txt)
        if txt:
            rows.append((t, txt))
    return rows

def extract_f0(wav, duration, fmin=80, fmax=1000):
    snd = parselmouth.Sound(wav)
    pitch = snd.to_pitch(time_step=F0_STEP, pitch_floor=fmin, pitch_ceiling=fmax)
    f0 = np.asarray(pitch.selected_array["frequency"], dtype=float)
    n = int(round(duration / F0_STEP))
    if len(f0) < n:
        f0 = np.pad(f0, (0, n - len(f0)))
    f0 = f0[:n]
    k = 5
    pad = np.pad(f0, (k // 2, k // 2), mode="edge")
    f0 = np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=-1)
    voiced = f0[f0 > 0]
    if len(voiced) == 0:
        return [0.0] * n
    med = float(np.median(voiced))
    for i in range(len(f0)):
        if f0[i] <= 0:
            continue
        for _ in range(3):
            if f0[i] / med > 1.8:
                f0[i] /= 2
            elif f0[i] / med < 0.55:
                f0[i] *= 2
            else:
                break
    return [round(float(x), 1) for x in f0]

def align_full(official, asr_chars, asr_ts):
    """官方歌词全文 <- ASR 字序列，返回每个官方字的时间"""
    sm = difflib.SequenceMatcher(None, official, asr_chars, autojunk=False)
    out = [None] * len(official)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out[i1 + k] = [asr_ts[j1 + k][0] / 1000.0, asr_ts[j1 + k][1] / 1000.0]
        else:
            if j1 < len(asr_ts):
                t0 = asr_ts[j1][0] / 1000.0
                t1 = asr_ts[min(j2, len(asr_ts)) - 1][1] / 1000.0
            else:
                t0 = out[i1 - 1][1] if i1 > 0 and out[i1 - 1] else 0.0
                t1 = t0 + 0.3 * (i2 - i1)
            span = max(0.08, t1 - t0)
            for k in range(i2 - i1):
                out[i1 + k] = [t0 + span * k / max(1, i2 - i1),
                               t0 + span * (k + 1) / max(1, i2 - i1)]
    # 补空
    prev = 0.0
    for i, x in enumerate(out):
        if x is None:
            out[i] = [prev, prev + 0.2]
        prev = out[i][1]
    # 单调
    for i in range(1, len(out)):
        if out[i][0] < out[i - 1][1]:
            out[i][0] = out[i - 1][1]
        if out[i][1] <= out[i][0]:
            out[i][1] = out[i][0] + 0.05
    return out

def build_line(row, chars_ts, f0_seq, line_start, line_end, wav_dur):
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wav", required=True)
    ap.add_argument("--lrc", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", default="/data/pado/ds")
    ap.add_argument("--asr", default=None, help="缓存 asr json")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rows = parse_lrc(args.lrc)
    print(f"LRC {len(rows)} 行")

    # ASR
    if args.asr and os.path.exists(args.asr):
        r = json.load(open(args.asr))
    else:
        os.environ["MODELSCOPE_CACHE"] = "/data/ms_cache"
        from funasr import AutoModel
        m = AutoModel(model="paraformer-zh", vad_model="fsmn-vad", punc_model="ct-punc",
                      device="cuda", disable_update=True)
        r = m.generate(input=args.wav, sentence_timestamp=True, batch_size_s=200)[0]
        json.dump(r, open(args.asr or "/tmp/asr_cache.json", "w"), ensure_ascii=False)
    asr_chars, asr_ts = [], []
    for s in r.get("sentence_info", []):
        ts = s.get("timestamp", [])
        txt = [c for c in s.get("text", "") if "\u4e00" <= c <= "\u9fff"]
        if len(txt) != len(ts):
            n = min(len(txt), len(ts)); txt, ts = txt[:n], ts[:n]
        asr_chars.extend(txt); asr_ts.extend(ts)
    print(f"ASR {len(asr_chars)} 字")

    official = "".join(x[1] for x in rows)
    times = align_full(official, asr_chars, asr_ts)

    snd = parselmouth.Sound(args.wav)
    dur = float(snd.get_total_duration())
    f0_seq = extract_f0(args.wav, dur)

    idx = 0
    made = 0
    for i, (t, txt) in enumerate(rows):
        n = len(txt)
        chars_ts = times[idx: idx + n]
        idx += n
        t_next = rows[i + 1][0] if i + 1 < len(rows) else dur
        line_start = max(0.0, t - 0.05)
        line_end = min(dur, max(t_next - 0.02, line_start + 0.3))
        ds = build_line(txt, chars_ts, f0_seq, line_start, line_end, dur)
        if not ds:
            continue
        span = ds.pop("_span")
        # 切音频（前后各留 0.05）
        seg_start = max(0.0, line_start - 0.05)
        seg_len = min(dur - seg_start, span + 0.10)
        name = f"{args.tag}_L{i:03d}"
        seg_wav = os.path.join(args.out, name + ".wav")
        subprocess.run(["ffmpeg", "-y", "-ss", f"{seg_start:.4f}", "-t", f"{seg_len:.4f}",
                        "-i", args.wav, "-ar", "44100", "-ac", "1", seg_wav,
                        "-loglevel", "error"], check=False)
        with open(os.path.join(args.out, name + ".ds"), "w", encoding="utf-8") as f:
            json.dump([ds], f, ensure_ascii=False)
        made += 1
    print(f"DONE {args.tag} 生成 {made} 条")

if __name__ == "__main__":
    main()
