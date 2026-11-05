# 聂莫黎歌声数据集（DiffSinger 声库训练用）

《纸嫁衣》聂莫黎虚拟歌姬声库的**全部训练资产**。抓取 → 分离 → 切片 → 标注 → binarize 的成果都在这里，接手人不需要重跑前处理。

## 一、Release 里的大文件

| 文件 | 大小 | 内容 |
|---|---|---|
| `A_ds_labels_599.tar.gz` | ~193 MB | 599 条 `.ds` 标注 + 599 个切片 wav（16k 单声道）。解压得 `ds/`，`s01_L000.ds` / `s01_L000.wav` … `s12_Lxxx` |
| `B_sep_vocals_12.tar.zst` | ~210 MB | 12 首歌 UVR-MDX 分离人声，无损 FLAC 44.1k。解压得 `s01_vocals.flac` … `s12_vocals.flac` |
| `C_configs_scripts.tar.gz` | 48 KB | 配置 + 字典 + csv + 脚本 + lrc（本仓库里也有一份平铺的） |

## 二、仓库内文件

```
configs/       acoustic.yaml  duration.yaml  variance.yaml   # 已按 44.1k / 单说话人改好
dictionary/    niemoli.txt                                     # 601 行中文音素表，AP 行已删
labels/        transcriptions.csv                              # binarize 必需，599 行
scripts/       asr_song.py make_ds_song.py batch_ds*.sh ...     # 全流程脚本
lyrics/        s01.lrc … s11.lrc
```

## 三、还原 + 训练

```bash
tar -xzf A_ds_labels_599.tar.gz                    # -> ds/
tar -xzf C_configs_scripts.tar.gz                  # -> configs/ dictionary/ labels/ scripts/
zstd -d B_sep_vocals_12.tar.zst && tar -xf B_sep_vocals_12.tar   # -> *.flac

# 目录摆法（DiffSinger 要求）
mkdir -p data/niemoli_song/raw
cp -r ds/* data/niemoli_song/raw/          # 599 个 .ds + 599 个 .wav 同级
cp labels/transcriptions.csv data/niemoli_song/raw/
cp dictionary/niemoli.txt dictionaries/

# 二值化
python data/binarize.py --config configs/acoustic.yaml
python data/binarize.py --config configs/variance.yaml

# 训练
python tasks/acoustic_task.py --config configs/acoustic.yaml
python tasks/variance_task.py --config configs/variance.yaml
```

## 四、必须知道的坑

1. **这个 DiffSinger 版本没有 `duration_task.py`**，只有 `acoustic_task.py` 和 `variance_task.py`。时长由 variance 模型一起预测。
2. **binarize 只认 `raw/` 下的 `transcriptions.csv` + `wavs/`（或同级 wav）**，直接丢一堆 `.ds` 会报错。
3. **声码器要单独下**：`pc_nsf_hifigan_44.1k_hop512_128bin_2025.02`，从 `github.com/openvpi/vocoders/releases` 取 `model.ckpt` + `config.json`，放到 `checkpoints/pc_nsf_hifigan_44.1k_hop512_128bin_2025.02/`。原机器上这个路径是空的。
4. **字典里不能有 `AP` 行**，已删。若重跑 binarize 报 `AP not found`，检查这点。
5. variance 配置里 `predict_energy: false`、`predict_breathiness: false`，只出 duration + pitch，别改。

## 五、数据来源

- 12 首歌：QQ 音乐，AI 翻唱音源，UVR-MDX-NET Inst HQ3 分离
- 标注：`/data/pado/asr_song.py` 走 whisperX 对齐，人工未复核（这是已知风险点，599 条里可能有错字/错切）
- 音域/音质：44.1k 源，切片后 16k 训练

## 六、版权

角色与音源版权归《纸嫁衣》版权方及原演唱者。此仓库仅作**个人技术研究**用途，不得商用、不得二次分发音频。
