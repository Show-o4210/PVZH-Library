# 21. 全场变形、当前攻血与原生子效果

用于已授权的“变成指定卡并保留当前攻血”运行时任务。先读[第21章10](../Library-docs/21.语义调试与技能扩展实战/10.全场变形保留当前攻血与原生子效果/README.md)、[原实现记录](../Library-docs/21.语义调试与技能扩展实战/10.全场变形保留当前攻血与原生子效果/R25法老实现记录.md)及[筛选证据](../Library-docs/21.语义调试与技能扩展实战/10.全场变形保留当前攻血与原生子效果/法老技能验收摘要.json)，许可按[Agent16](16-experimental-capabilities-and-launch.md)，证据按[Agent11](11-semantic-testing-and-evidence.md)。

- 先确认语义：保留的是每个目标当前Attack与当前HP；原7攻/最大13HP/伤3变为7攻10HP、伤害0。owner/lane走原生变形，费用/种族/词条/技能采用目标定义。英雄、手牌、牌库、环境和源卡是否排除需写清。
- 多目标先做同批快照，再逐目标变形；旧光环中途消失不应污染其余目标的原始快照。模型、effect指针、generation与实体有效性必须绑定当前对局。
- 1026是Android R25 pharaoh RC5的私有规则，运行支持不等于AI自由配方或公开Python v1支持；不跨版本套RVA、规则号、字段布局。
- 私有处理器生成的子效果若继承旧EffectEntityId，会被原PlayTrigger重验取消；仅关闭目标重验不够。本例已自行精确验证目标，才窄用EffectEntityId=-1/RequiresTargetValidation=false，Source/Springboard仍真实。不能推广为全局跳过验证。
- 原版普通僵尸GUID50含cheats标签；随机Subset Finder的NotCheats限制与“指定GUID变形”不同。复用已核对的原router/handler/TransformSystem指定卡入口，不删除全局标签、不另造System、不只改GUID。
- 等真实ContinuousEffectsCompleteEffect边界后按已生效环境/光环补偿一次。负HP窗口只保护本次原正生命快照、先于CheckDeath，结束立即解除；后续Buff与致命伤必须仍生效。不要长期锁属性、循环泵队列或新增重复Hook。
- 看当前属性、伤害履历、TransformedCard、owner/lane、环境/光环、墓碑、法老自身、手牌/英雄、原版入口与后续致死分别留证。不要用队列空或音乐启动代替技能结算。
- 音乐独立复用已登记1024/1025与当前Mod曲目，流程见[Agent20](20-local-music-capability.md)。MediaPlayer真实进度/RTPC与扬声器听验分开；系统音量0时不能宣称已听验。

本例RC5真实基础54、正环境78、负环境79、原版10，共221检查通过。RC1子效果验证失败、RC2只构建未测、RC3 NotCheats失败、RC4基础52通过但环境重复Buff失败均保留。无截图/点击；视觉未逐帧、扬声器未听验、warm restart彻底清理未确认。R26及其他候选不在本例PASS范围。此页与摘要不携带完整runtime、APK、原始设备日志或WAV。
