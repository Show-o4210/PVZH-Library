# Wwise 游戏音频替换工具

本项目现位于 [PVZH-Library](../../README.md) 的 `tools/audio-tool/`，独立依赖与运行方式保留。

从主仓库根目录进入本项目后，再执行下方安装和运行命令：

```bash
cd tools/audio-tool
```

**源码与完整包**：Git 源码树包含 Python 脚本与配置；下文所述 BAT、`zSound2wem.cmd`、FFmpeg 和 vgmstream 位于 [原完整 Windows 工具包](https://github.com/Show-o4210/PVZH-audio-tool/releases/tag/%E5%AE%8C%E6%95%B4)。下载后解压到本目录，并保留本仓库较新的 Python 脚本、配置与 README。归档旧仓库后，此下载入口仍保留。

源码命令行入口（解包需自行准备 vgmstream，打包还需 FFmpeg、Wwise 和转换脚本）：

```bash
python -m pip install UnityPy
python pipeline.py extract
python pipeline.py build
```

一键化解包、试听、替换、回包 Unity 游戏 AB 包中的 Wwise 音频。  
全程通过 **UnityPy** 读写 AB 包，**无需 UABEA**。

---

## 快速开始

```text
1. 安装依赖：Python 3、UnityPy、Wwise（见下方说明）
2. 将游戏 AB 包放入 input/ab/
3. 双击 1-解包试听.bat
4. 试听 output/extracted/<项目名>/wav/ 中的音频
5. 将替换音频放入 input/replace/<项目名>/，按序号命名（如 001.mp3）
6. 双击 2-打包输出.bat
7. 用 output/modified/<项目名>_modified 替换进游戏
```

---

## 目录结构

```text
项目根目录/
├── 1-解包试听.bat              # 第一步：解包 + 解码试听
├── 2-打包输出.bat              # 第二步：替换 + 转 WEM + 回包
├── pipeline.py                 # 流水线主脚本
├── repack_bnk.py               # 底层 Bank 工具（高级手动入口）
├── zSound2wem.cmd              # 外部音频 → .wem 转换（需 Wwise）
├── config.json                 # 可选音频转换参数
│
├── input/
│   ├── ab/                     # ← 放入游戏 AB 包
│   └── replace/                # ← 放入替换音频（按序号命名）
│
├── output/
│   ├── extracted/              # 解包产物（自动生成，请勿手动修改）
│   └── modified/               # 成品 AB 包（可直接替换进游戏）
│
├── ffmpeg-8.0.1-essentials_build/   # FFmpeg（已内置，用于格式转换）
│   └── bin/ffmpeg.exe
├── vgmstream-win64/            # WEM 解码工具（已内置）
│   └── vgmstream-cli.exe
└── README.md
```

> 首次打包时，`zSound2wem.cmd` 会在项目根目录自动创建 `wavtowemscript/`（Wwise 转换工程），属于正常运行产物，无需手动处理。

---

## 环境依赖

| 组件 | 是否已内置 | 说明 |
|------|-----------|------|
| Python 3.x | 需自行安装 | 运行所有脚本 |
| UnityPy | 需自行安装 | `pip install UnityPy` |
| vgmstream | 已内置 | `vgmstream-win64/` |
| FFmpeg | 已内置 | `ffmpeg-8.0.1-essentials_build/` |
| Wwise | 需自行安装 | [Audiokinetic 官网](https://www.audiokinetic.com/) 下载安装 |

- **解包**：需要 Python + UnityPy + vgmstream（均已就绪或一条 pip 命令）
- **打包**：额外需要本机已安装 Wwise（zSound2wem 调用 WwiseConsole 转换）

---

## 替换音频命名规则

解包后，每条音频会按顺序重编号为 `001`、`002`、`003`……

| 文件 | 说明 |
|------|------|
| `output/extracted/<项目名>/wav/001.wav` | 第 1 条音频，用于试听 |
| `output/extracted/<项目名>/index.txt` | 序号与原始 Wwise ID 的对照表 |
| `output/extracted/<项目名>/manifest.json` | 完整映射数据（脚本内部使用） |

在 `input/replace/` 中按**序号**放置替换文件：

```text
input/replace/<项目名>/001.mp3     ← 替换第 1 条
input/replace/<项目名>/003.wav     ← 替换第 3 条
```

规则：

- **只放要替换的序号**，未提供的条目自动保留原版
- **格式不限**（`.wav` `.mp3` `.ogg` `.flac` 等均可），打包时由内置 FFmpeg 自动转为标准 WAV
- 若只有一个 AB 包，也可直接放在 `input/replace/` 根目录（如 `001.mp3`）
- 序号请对照 `output/extracted/<项目名>/index.txt`

`index.txt` 示例：

```text
001  id=72198416  size=5126  duration=1.22s  wav=001.wav
002  id=103099345  size=6680  duration=1.63s  wav=002.wav
```

---

## config.json 配置

```json
{
  "samplerate": "",
  "channels": "",
  "volume": "",
  "conversion": "Vorbis Quality High",
  "ffmpeg": ""
}
```

| 字段 | 说明 |
|------|------|
| `samplerate` | 目标采样率（Hz），留空保持源文件 |
| `channels` | 目标声道（`1`=单声道，`2`=立体声），留空保持源文件 |
| `volume` | 音量，支持倍率（`1.5`）或分贝（`3dB`） |
| `conversion` | Wwise 编码质量，默认 `Vorbis Quality High` |
| `ffmpeg` | FFmpeg 路径，留空则自动搜索项目内 `ffmpeg*/bin/ffmpeg.exe` |

---

## 工作流程

### 阶段一：解包（1-解包试听.bat）

```text
input/ab/ 中的 AB 包
  → UnityPy 读取内部 Wwise Bank
  → 提取 WEM，重命名为 001.wem, 002.wem ...
  → vgmstream 解码为 001.wav, 002.wav ...
  → 生成 manifest.json + index.txt
  → 输出到 output/extracted/<项目名>/
```

### 阶段二：打包（2-打包输出.bat）

```text
input/replace/<项目名>/001.mp3
  → 内置 FFmpeg 规范化为标准 WAV
  → zSound2wem.cmd + Wwise 转换为 001.wem
  → 重包 Bank（16 字节对齐 + DIDX 索引重建）
  → UnityPy 写回 AB 包
  → 输出到 output/modified/<项目名>_modified
```

---

## 高级手动入口

如需逐步手动操作，可运行：

```bash
python repack_bnk.py
```

支持单独解包、解码、回包，以及 UnityPy 导出/导入 `.bytes`，适合调试或特殊场景。

---

## 常见问题

### Q: 重包后的 AB 包体积变大了？

UnityPy 重存 AB 时压缩策略可能与原版不同，体积变大属正常现象。只要游戏能正常加载即可使用。

### Q: 可以把 WAV 直接放进 wem 目录吗？

不可以。请将替换音频放入 `input/replace/`，流水线会自动完成 FFmpeg → Wwise → WEM 的全流程转换。

### Q: 打包提示找不到 Wwise？

请先安装 Wwise，并确认安装后系统存在 `WWISEROOT` 环境变量。zSound2wem 依赖 WwiseConsole 进行编码，此步骤无法跳过。

### Q: 打包提示找不到 FFmpeg？

本项目已内置 `ffmpeg-8.0.1-essentials_build/`。若移动了目录结构，可在 `config.json` 中手动填写 `ffmpeg` 的完整路径。

### Q: 一个 AB 包里有多个 Bank？

脚本会自动识别，每个 Bank 在 `output/extracted/` 下生成独立子目录。替换音频也需放入 `input/replace/` 下对应的项目子目录。

### Q: 解包后的 extracted 目录可以删除吗？

可以。下次运行「1-解包试听.bat」会重新生成。但重新解包后需确认 `input/replace/` 中的序号仍与新的 `index.txt` 一致。

---

## 打包分发本工具时

以下内容**无需**发给最终用户（使用过程中会自动生成，或属于个人测试残留）：

- `output/extracted/<项目名>/`（解包产物）
- `output/modified/*_modified`（成品 AB 包）
- `wavtowemscript/`（Wwise 转换工程，首次打包自动创建）
- `input/ab/` 中的游戏 AB 包
- `input/replace/` 中的个人替换音频

保留本项目根目录下的脚本、bat、`config.json`、`ffmpeg-*`、`vgmstream-win64/` 及 `input/`、`output/` 中的说明占位文件即可。

---