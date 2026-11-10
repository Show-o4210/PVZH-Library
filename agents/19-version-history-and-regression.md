# 19. 连续创作、真实历史与普通表达验收

用于Android R24后续的历史差异、整版回退、单次bulk撤销、单位筛选目录和普通玩家回归。先读[第22章11](../Library-docs/22.自然语言原版制卡/11.版本历史与普通表达回归.md)及[筛选摘要](../Library-docs/22.自然语言原版制卡/连续创作验收摘要.json)。批量属性与字段分类继承[Agent18](18-batch-stats-and-typed-review.md)，会话审批继承[Agent17](17-conversation-authoring-and-approval.md)。

## 操作原则

1. 校验当前Mod ID、卡牌命名空间、源ZIP SHA及稳定索引指纹；同ZIP不保证同手动映射。
2. 从真实历史原件生成新revision的待审候选，不覆写旧历史，不直接更新已保存Mod。审批后仍需冷启动加载。
3. 单次撤销必须取得该批次真实输入并重放，账本before值和“已撤销”文字不是证明。
4. CAS核对当前值，并检查后续同字段写、current/base读和数值selector依赖。筛选依赖覆盖原先未命中但撤销后可能进入的卡；冲突不给部分结果。
5. 只恢复实际改动字段。最小新增Attack需要校验后移除，已扩展的组件不能盲删。保留后续无关技能、CN、关卡和资源。
6. 查当前目录再用种族/稀有度/卡集/职业字符串。根rarity3=R4传说，根rarity4=R0；不猜Subtype数字，不混淆Token与不可收藏。
7. 普通话术回归只发送prompt与正常项目上下文，不把独立期望where/effect交给模型。Oracle看真实产物，不信作者自己说PASS。
8. 数据、协议、真实API、设备界面和战斗结算分开；历史/音频不能只凭卡表JSON验成功。

当前证据：历史两种JSON各48/512MiB、双快照热路径各7/256MiB、映射24；Pixel协议25及UI5。筛选各12453与旧1241、六项golden保持。30定义中19批量数据交叉检验；真实API只执行八条，最终通过且保留n10内部修订，不说30次API全过。

保留R23审查OOM以及R24宽夹具256MiB OOM。不能把512MiB宽集或256MiB热路径外推为所有Pixel或大Mod的内存保证。音乐另读[Agent20](20-local-music-capability.md)，运行时许可和AI许可分别核对。
