# 09. 本地背景音乐与共享生命周期

本节记录Android R24为“招笑版”设计者提出的音乐技能搭建的受控能力：原游戏BGM临时静音，同时播放当前Mod已登记的本地音频。原音乐事件继续运行，恢复时回到原游戏当前编排；不替换音频银行，不将系统媒体流音量设0，也不改SFX。

这是已授权的私有运行时扩展，**不是原版卡表自带能力，也不是公开Python v1新功能**。字段与证据见[音频能力验收摘要](音频能力验收摘要.json)。截至本页当前记录，静态/协议通过；RC3设备被保护性拒绝，RC4实际播放/解码通过、恢复断言未过；RC5音乐原引擎18检查、原版隔离冷启动10检查通过，实际听验未做。

## 曲目与技能分别登记

Mod ZIP以`audio/music.json`登记曲目id、标题、相对source、SHA256、大小、loop和gain，音频源限定在Mod内`audio/`下的wav/ogg/mp3。路径越界、URL、绝对路径和外部代码不接受。模型只能引用当前Mod已校验曲目的`track_id`，不能凭空生成路径或宣称未导入曲目存在。

启动器校验并流式提取到固定app-private目录，以文件SHA命名；最终`active.json`绑定本次资源事务ID与`r24-capabilities-1`。slot由卡牌身份命名空间与track_id的SHA256前三字节确定，0映射为1；碰撞按启动器靠前优先并提示，不以随机覆盖解决。原版启动不会沿用Mod曲目。

运行需要`extensions_enabled`与`music_enabled`，AI创作还需独立AI能力许可。登记、冻结启动许可、实际安装/播放是三层状态，不把“菜单已开启”当作音乐已经响起。

当前两个单位配方：

| 能力 | 私有规则 | 参数 |
|---|---:|---|
| `pvzh.rule.music_play` | 1024 | 当前已登记`track_id`，可选`trigger=play/turn_start` |
| `pvzh.rule.music_restore` | 1025 | 可选`trigger=play/turn_start` |

建议以extension append保留原技能。编译器使用原版触发器与Grant描述符承载已登记规则；这不授权AI创建任意Grant编号。初版未开放任意受伤/死亡/锦囊/环境触发组合。

只作格式参考的单卡增量示例：

```json
{"guid":10,"extension":{"mode":"append","recipes":[{"id":"pvzh.rule.music_play","params":{"track_id":"battle","trigger":"play"}}]}}
```

使用前必须从当前Mod确认GUID10的真实对象，并已登记battle；示例不是可脱离原件直接导入的完整计划。技能中文应说明真实曲目与触发，移除/替换配方时迁移旧自动句，不借文字冒充没有写入的效果。

## 等效切换的握手

```mermaid
flowchart LR
    A[原版事件产生已登记Grant] --> B[核对事务和曲目]
    B --> C[后台校验大小与SHA]
    C --> D[MediaPlayer准备成功]
    D --> E[Unity线程临时设音乐RTPC为0]
    E --> F[带同一request_id启动播放]
    F --> G[停止、失败或生命周期结束]
    G --> H[释放播放器并恢复原音乐RTPC]
```

文件未验证或尚未prepare时保留原BGM。取消后晚到的prepare回调不能再启动；请求ID、事务与model generation共同隔离旧任务。开始失败、解码错误、准备超时和非循环结束会恢复原音乐；恢复短暂失败保留帧重试通路。

读取MixManager当前音乐期望值，以其比例调整自定义增益；用户关闭音乐时，自定义音乐同样静音。**不能调用SetMusicVolume(0)来冒充临时静音**：该函数会改MixManager保存的期望字段。实现只临时设置`MUSIC_VOLUME_RTPC`，不覆盖用户音乐偏好。

Java MediaPlayer在主Looper串行管理；校验逐块进行并交付已打开描述符，避免全曲读入内存。它不另请求AudioFocus，避免同UID的Wwise被第二次focus整体暂停。后台由Activity与Unity暂停观察协作；前台不由Java自行恢复播放，重新完成RTPC/start握手。

## Hook应复用实际owner

当前1.67.8 arm64依据包括MixManager、AkSoundEngine音乐RTPC、用户MusicVolume字段和Unity暂停回调。RVA、字段布局与五处签名先核对匹配二进制，不能复制到其他版本。

RC3设备安装音乐模块时报告`Mod audio native signature mismatch: home`：返回主页方法`0x1B23434`在本进程已被旧v6入口观察，内存前缀因此不同。这个地址的owner是v6资源UI回调，不能因为原dump有RVA就再安装一次Hook。

保护性拒绝发生在播放之前：模块未安装、actions=0、原BGM未静音，系统音量和音乐设置未写，进程继续存活。原引擎报告保留为SEMANTIC_FAIL，不称成功播放。

RC4修复采用共享既有主页owner：保留原`setHomeVisible(true)`，在同一回调调用音乐reset；不放宽其他五处音频签名检查，也不在已Hook地址上要求原始前缀。RC4已确认共享入口可安装；恢复流程另暴露下述问题，不能把安装通过扩展为整套验收通过。

## 怎样分别验收

| 层次 | 能证明什么 | 当前记录 |
|---|---|---|
| SDK编译 | Java/API引用可编译 | 通过 |
| host Java协议 | 哈希/取消/准备失败/前后台/主Looper顺序 | 两种JSON各61检查通过；stub不是解码器 |
| JS状态模型 | 事务、准备前不静音、恢复、竞态处理 | 最终94检查通过；不是Wwise实测 |
| 配方与Bundle回读 | 已登记曲目写入、权限/路径拒绝、CN及非目标保留 | 两种JSON各687检查通过 |
| 生成bundle接线 | 唯一Grant分派、外层许可、共享生命周期入口 | 最终39检查通过；不是实际发声 |
| RC3原引擎 | guard能在冲突地址前拒绝、保持未静音 | 保护性拒绝，FAIL保留 |
| RC4实际播放 | 合法出牌、原音乐RTPC0、MediaPlayer进度0→705ms/时长12000ms | 此范围通过 |
| RC4恢复 | 恢复技能后的真实RTPC | 未通过：控制器idle/未静音标记，但回读仍0 |
| RC5原引擎 | 合法播放、真实后端、恢复、前后台、音量与存活 | 18检查通过，恢复后帧回读RTPC100 |
| RC5原版隔离 | 原版冷启动不安装Mod音乐、不残留播放 | v2场景10检查通过 |
| 扬声器可听输出 | 真实可听声音 | 未验证 |

RC4报告有12项通过、1项恢复失败，进程继续存活。正常播放已取得真实后端进度；恢复阶段却在AKSuccess之后立即把控制器标成idle/未静音，实际RTPC仍读到0。请求被接受不等于音频线程已经应用，既不能把这条失败改成PASS，也不能据此宣称永久静音或崩溃。RC5拟保留restore_pending并在后续帧回读确认。

后台项同样需要更严格的证据：当场控制状态是paused且原静音标记已清，但native.rtpc仍0、backend_is_playing可能是暂停前缓存值。因此原报告该项PASS只覆盖控制流程，不能当作真实后台暂停和原音乐恢复已经完成；复验要等待新的backend_sampled_at、后端false和目标RTPC。

RC5保留restore_pending到后续帧真正回读目标RTPC，18个原引擎检查通过。使用未手改的同一AI候选（SHA见摘要），合法打出后RTPC为0，真实MediaPlayer从0推进至798ms、总长12000ms；恢复技能后确认RTPC100、pending清除、播放器释放，同进程存活且当场crash buffer为空。

后台复验等待新的backend_sampled_at，确认MediaPlayer真实isPlaying=false且foreground=false；此时原音乐恢复仍为pending，只把该项记为“恢复已请求”，不谎称后台物理RTPC已更新。前台通过握手继续播放，后续恢复技能的真实100回读另行确认。

系统媒体流音量测试前后均为0（范围0～25），游戏音乐偏好100未改。测试没有擅自提高手机音量，因此本轮证明解码、播放进度和控制链，**不证明扬声器已经听验**。当前12秒素材为本机生成的原创诊断旋律，Library不附带音频文件。

原版隔离采用新的冷进程：active登记为空、原版标记true，运行时许可与音乐模块均关闭；原版豌豆仍1费1/1，合法打出音乐actions=0、无静音，同进程存活且crash buffer为空，10检查通过。首轮已通过5个隔离检查，但测试脚本在live PvE创建之前读card_info而得到FRAMEWORK_ERROR；进程仍存活。修正前置顺序后以v2冷进程复验，保留首轮，不算游戏崩溃或抹掉失败。

`state="playing"`只是控制器状态，不足以证明后端实际启动。设备应等待真实getter的`backend_sampled_at`更新，核对`backend_is_playing`、duration与position推进，再回读真实RTPC=0/恢复。即使这些通过，也不能自动升级为扬声器已经人工听验。

播放器最多128条、单曲32MiB、登记总量256MiB；每Mod另有更小限制，编辑器还继承47MB ZIP/128MB展开限制。这些上限取交集，不能只看播放器总量就承诺AI编辑器能处理相同大小素材。

本库不包含音频、游戏资源、完整运行时、APK或凭据。本机AUDIO-API说明（`pvzh-launcher/native-r24/docs/AUDIO-API.md`）为旧工程记录，本节及筛选摘要可独立阅读。

上述旧工程已退役，文件名保留作出处。可查仍保留的 [音频能力验收摘要](音频能力验收摘要.json)。
