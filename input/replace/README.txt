将替换音频放在此目录，文件名必须使用解包生成的【序号】。

示例：
  Guacodile/001.mp3
  Guacodile/003.wav

规则：
  1. 只需放入要替换的序号，未放入的音频会保留原版。
  2. 支持 .wav .mp3 .ogg .flac 等常见格式，打包时会自动转换。
  3. 序号请对照 output/extracted/<项目名>/index.txt。

若只有一个 AB 包，也可以直接放在本目录根部：
  001.mp3
  002.wav