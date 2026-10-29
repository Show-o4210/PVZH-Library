# 20. 当前Mod本地背景音乐能力

用于Android R24的已授权音乐技能。先读[第21章09](../21.语义调试与技能扩展实战/09.本地背景音乐与共享生命周期/README.md)和[筛选证据](../21.语义调试与技能扩展实战/09.本地背景音乐与共享生命周期/音频能力验收摘要.json)，再按[Agent16](16-experimental-capabilities-and-launch.md)区分登记/冻结/实际状态；语义证据按[Agent11](11-semantic-testing-and-evidence.md)。

- 原BGM临时音乐RTPC静音＋当前Mod登记的MediaPlayer本地曲目；不改系统媒体音量/SFX/用户音乐期望值，不替换银行。
- `audio/music.json`提供真实曲目来源、SHA、大小等；AI只引用已登记track_id，不接受URL、绝对路径或新Hook。原版/缺曲目/许可关闭不能宣称已生效。
- 运行需extensions_enabled与music_enabled；AI创作再核对独立AI许可。当前只开放单位play/turn_start的music_play(1024)、music_restore(1025)，不推断更多事件已可用。
- prepare成功并核对request/transaction/model后才静音原BGM；失败、取消、后台、主页、终局、model变化应恢复。晚到回调不能复活旧播放。
- 多模块Hook先查实际owner，不在同一已Hook方法再次要求原始字节或重复安装。RC3主页guard拒绝保留；RC4共享原v6主页回调的修复、播放通过与恢复失败分开登记。
- 控制器playing、MediaPlayer真实getter/position、Wwise实际RTPC和扬声器听验是不同证据，不能互相替代。

当前归档：静态、host协议和编译回读通过；RC3实际设备保护性拒绝、未静音且存活；RC4真实播放/进度确认，但恢复断言未过，后台控制PASS也没有充分真实回读；RC5实际音乐18检查通过、恢复后帧读到100、后台真isPlaying=false；原版隔离v2冷启动10检查通过，首轮harness前置错误保留；系统媒体音量前后0，可听输出未验。后台物理RTPC在暂停当场只确认恢复pending/requested，后续恢复技能才真实读到100；不要扩大范围。收到新收据后只补对应层次，不覆盖RC3/RC4失败。

本库公开Python v1未升级，且不附带完整服务或音频。源码中出现配方ID/RVA也不等于当前设备已安装；必须取得匹配二进制和原件再核对。
