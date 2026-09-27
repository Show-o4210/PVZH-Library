# 19. 良性 Mod 实战：离线卡组分享与编解码协议规范

在前面的章节中，我们已经掌握了全套动态运行时插桩与 Android 原生浮窗开发能力：
- 第 15 章教会了我们如何**定位 IL2CPP 内存符号与 RVA 偏移**；
- 第 16 章教会了我们如何**将代码打包成免 Root 独立 APK**；
- 第 17 章教会了我们如何**利用 UnityDispatcher 保证主线程调用安全**；
- 第 18 章教会了我们如何**在游戏顶层绘制现代化交互浮窗**。

现在，我们迎来了整套动态系列的**集大成篇章** —— **构建一个完整、工业级且绝对合规的“离线卡组分享助手（Deck Share Mod）”**。

在《植物大战僵尸：英雄》原版游戏中，玩家之间一直饱受“无法一键分享和导入卡组”的困扰。传统的交流方式是截图一张长长的 40 张卡牌图片，接收方对着图片在游戏卡册里一张张手动查找、比对、拖拽，极其繁琐。

本章节将公开一套完整的 **`PVZH1:` 离线卡组编解码标准**，深入拆解高容错文本解析器、客户端拥有权合规校验，以及如何通过官方原版 `PlayerDeckProviderImpl` 机制实现零风险的本地持久化。

---

## 目录导航

| 序号 | 专题文档 | 核心涵盖内容 |
| :---: | :--- | :--- |
| **01** | [01. 离线卡组分享协议设计与 Base64URL 编码](01.离线卡组分享协议设计与Base64URL编码.md) | 详解 `PVZH1:` 协议报文结构、JSON 载荷压缩设计、Base64URL 安全字符集以及高容错装饰性文本解析算法。 |
| **02** | [02. 卡牌合法性校验与未拥有资产过滤](02.卡牌合法性校验与未拥有资产过滤.md) | **合规基石**：严格单卡 4 张上限约束、英雄阵营与职业合法性矩阵、动态读取本地卡库并自动跳过未拥有卡牌的优雅降级设计。 |
| **03** | [03. 原生 Provider 调度与持久化写入实战](03.原生Provider调度与持久化写入实战.md) | 详解为何绝对不能硬写本地文件、挂载 `CreateNewCustomDeck`、`SaveOverDeck` 写入卡牌与 `PersistChanges` 原版持久化全流程。 |
| **04** | [04. 牌组双向导出与人性化清单生成](04.牌组双向导出与人性化清单生成.md) | 详解逆向读取已保存卡组、按费用/GUID 双重排序算法、多语言本地化卡名匹配与社交媒体友好型清单格式生成。 |

---

## 核心架构与数据流全景图

```mermaid
graph TD
    subgraph 玩家输入与协议解析 (Import Pipeline)
        A["玩家从剪贴板粘贴文本<br/>(支持带注释文本/纯代码)"] --> B["容错解析器 (Tolerant Parser)<br/>提取 PVZH1: 前缀与 Base64URL 载荷"]
        B --> C["JSON Schema 解码与基础反序列化<br/>提取 {v, name, hero, cards[[guid,count]]}"]
    end

    subgraph 合规校验与资产过滤 (Compliance Filter)
        C --> D["单卡最多 4 张上限校验<br/>自动截断超额卡牌"]
        D --> E["阵营与职业兼容性校验<br/>过滤不属于该英雄的跨阵营卡牌"]
        E --> F["本地已拥有库存核验 (PlayerInventory)<br/>自动跳过未拥有的卡牌，生成友好反馈清单"]
    end

    subgraph 原生持久化与界面刷新 (Native Provider Commit)
        F --> G["UnityDispatcher.runOnUnityThread<br/>投递至 UnityMain 主线程"]
        G --> H["调用 PlayerDeckProviderImpl.CreateNewCustomDeck<br/>生成合法的官方全局 UUID 与数据模型"]
        H --> I["调用 DefaultDeckEditorDeckSaver.SaveOverDeck<br/>将过滤后的合法卡牌序列写入模型"]
        I --> J["调用 MarkDeckAsModified & PersistChanges<br/>触发官方原有持久化与卡册 UI 自动刷新"]
    end
```

---

> [!NOTE]
> 💡 **“良性 Mod”的最高准则**：
> 1. **零特权越界**：本 Mod 不修改游戏数值，不向云端发包；
> 2. **完全尊重规则**：未拥有的卡牌绝不强行注入，游戏原本的卡牌收集乐趣与商业规则不受破坏；
> 3. **依托官方通道**：所有写入动作全部调用游戏内置的 `PlayerDeckProviderImpl` 完成，避免直接篡改文件引发的哈希冲突与数据损坏。
