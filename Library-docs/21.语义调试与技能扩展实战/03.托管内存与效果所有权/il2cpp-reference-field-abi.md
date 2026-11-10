# IL2CPP 引用字段赋值 ABI 核对

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/il2cpp-reference-field-abi.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

本文件记录 2026-10-14 的只读二进制核对，以及主运行时 R14 已采用的修正。引用字段的参数错误已通过本机实际机器码确认；后续主代理的 R14 实机回归已完成 14 个核心攻击用例与 7 条动作断言，全部 PASS。不能因此为全部历史 AssetGarbageCol 崩溃指定同一个原因。本次文档工作未操作 ADB，也未修改编译源。

## 已确认的问题与正确调用

当前 ARM64 二进制的 `il2cpp_field_set_value(obj, field, value)` 对引用字段接收**对象指针本身**，对数值字段接收**数值所在内存的地址**。旧版 `runtime.setField` 的 pointer 分支先创建 8 字节缓冲区，把对象指针写进缓冲区，再把缓冲区地址传给 field_set_value。这会把缓冲区地址本身写进 String 字段。

R14 主运行时为 pointer 分支使用专用的 `il2cpp_field_set_value_object(obj, field, value)`，直接传入托管对象指针；int/bool/u64 分支仍先写数值缓冲区，再使用 `il2cpp_field_set_value`。概念调用如下：

```javascript
// String / managed object reference
api.fieldSetObject(obj, field(obj, name), value);

// int32 / bool / uint64 value
api.fieldSet(obj, field(obj, name), numericBuffer);
```

这里的 pointer 分支指托管引用字段，不能把真正的 IntPtr 或其他值类型字段按托管引用处理。

## 二进制来源与地址

参考 ELF：`D:\Codex\PVZH\dump\libil2cpp.so`，游戏版本 1.67.8 ARM64。

SHA256：`18178B2F35959BC3954378A9778CDDD67AAB8A7EF22579EA59D736521EEC8C91`。

类型与字段对照：同目录 `dump.cs`；原版方法地址对照：`script.json`。导出入口从 ELF `.dynsym` 读取，反汇编使用本机 Capstone。下表全部为 RVA；代码文件偏移应按 ELF PT_LOAD 映射，本文件涉及的执行段为 RVA 减 0x4000。只读跳转表必须按其自己的 PT_LOAD 映射，不能套用执行段偏移。

| 导出 / 内部路径 | RVA | 核对结果 |
|---|---|---|
| il2cpp_field_set_value | 0x17CFD1C | 单条跳转到 0x179FE34 |
| field_set_value 内部入口 | 0x179FE34 | 从 FieldInfo+0x18 取字段偏移，从 FieldInfo+0x08 取字段类型，w3 置 0；第三参数 x2 不变 |
| 按字段类型赋值的公共分发器 | 0x179F6EC | x20 保存第三参数，w21 保存是否解引用开关；根据类型跳转 |
| 引用类型分支 | 0x179F77C | w21 为 0 时跳过 `ldr x20,[x20]`，直接使用 x20 作为引用值 |
| 引用写入与写屏障入口 | 0x17D368C | `str x1,[x0]` 写入对象指针，再跳转 GC 写屏障 0x180E90C |
| il2cpp_field_set_value_object | 0x17CFD20 | 单条跳转到 0x179FF6C |
| 专用对象字段赋值内部入口 | 0x179FF6C | 目标为 obj+字段偏移，传入对象指针直接作为 x1，进入 0x17D368C |

`field_set_value` 的入口和引用分支关键指令：

```text
0x179FE34  ldrsw x9, [x1, #0x18]   ; FieldInfo.offset
0x179FE38  ldr   x8, [x1, #8]      ; FieldInfo.type
0x179FE3C  mov   w3, wzr           ; 引用值不解引用
0x179FE40  add   x1, x0, x9        ; 字段写入位置
0x179FE44  mov   x0, x8
0x179FE48  b     0x179F6EC

0x179F6FC  mov   x20, x2          ; 保留原第三参数
0x179F70C  mov   w21, w3
...
0x179F77C  tbz   w21, #0, 0x179F784
0x179F780  ldr   x20, [x20]       ; 此 API 的引用路径跳过本行
0x179F784  mov   x0, x19          ; 字段位置
0x179F788  mov   x1, x20          ; 直接传入原第三参数
0x179F798  b     0x17D368C

0x17D368C  str   x1, [x0]
0x17D3690  b     0x180E90C        ; GC 写屏障
```

ROVA `0xD5F10C` 的跳转表已读取，分发索引为 `type - 2`，目标为 `0x179F738 + table[index] * 4`：

| IL2CPP 类型 | 类型编号 | 表项 | 目标与读取方式 |
|---|---|---|---|
| String | 14 / 0x0E | 0x11 | 0x179F77C，直接对象指针 |
| Class | 18 / 0x12 | 0x11 | 0x179F77C，直接对象指针 |
| Object | 28 / 0x1C | 0x11 | 0x179F77C，直接对象指针 |
| Int32 | 8 / 0x08 | 0x22 | 0x179F7C0，`ldr w8,[x20]` 读取缓冲区内 4 字节 |
| Boolean | 2 / 0x02 | 0x1C | 0x179F7A8，`ldrb w8,[x20]` 读取缓冲区内 1 字节 |

专用 `field_set_value_object` 入口只有以下字段地址计算，随后同样走写屏障：

```text
0x179FF6C  ldrsw x8, [x1, #0x18]
0x179FF70  mov   x1, x2           ; 托管对象指针，未解引用
0x179FF74  add   x0, x0, x8
0x179FF78  b     0x17D368C
```

## GroupId 的受影响路径

| 路径 | 写入字段 | 后续原版用途 |
|---|---|---|
| runtime.debugEffect 的 BuffEffect fixture | BuffEffect.GroupId，0x50 | BuffSystem 把分组传入 IntModifier；数值复位 / CopyStats 的 strip 路径会读取并解析分组 |
| mod2-attack 的 1008 狗头攻击英雄后 -3/-3 | BuffEffect.GroupId，0x50 | 同样生成原版属性 modifier，后续属性重置可进入分组读取路径 |
| mod2-skills 的 1012 下回合扣阳光 | GainSunEffect.GroupId，0x50 | 原版阳光 modifier 保存分组，按 EndOfTurn / Immediate 的生命周期处理 |

IntModifier.GroupId 是 0x10 的 String 引用。`StatUtils.StripNonContinuousModifiers` 在 RVA `0x21D39E0` 调用 `Int32.Parse(GroupId)`，随后查询 EntityModel，再通过 EffectEntityUtils.IsContinuousEffect 区分是否保留持续 modifier。普通卡牌 ID 字符串是有效分组，普通卡通过原版 HasComponent&lt;Continuous&gt; 查询返回 false；与这个内容契约无关的是引用参数必须指向真正的托管 String。

曾有两项独立问题，不能混淆：

1. BuffEffect 默认空分组不能通过 `Int32.Parse`，会使 strip 路径抛异常；使用数字实体 ID 解决内容问题。
2. 数字字符串通过错误参数层级写入时，字段实际上收到原生临时缓冲区，仍然不是托管 String；R14 修正引用 ABI。

旧写法中缓冲区的首个机器字是 String 对象指针。GC 若把缓冲区地址当对象地址，会把这个首字进一步当作 class 指针解释。这提供了与 AssetGarbageCol / IL2CPP liveness 遍历遇到无效 class 相符的具体机制；ABI 写坏已经确认，但各次崩溃的因果归属仍须设备对照验证。

直接比较历史已编译包也有边界：r5 的前十项攻击验证通过，其 runtime 没有 fixture Buff 的 GroupId 赋值；已编译 r6 同样尚无这条 fixture 赋值，且另外引入过 History 全局观察器。因此不能把所有 r6 及后续失败统一归为这一项。r5/r6/r12 的 stat/damage 模块逐行完全一致，没有标量字段偏移或 dirty 回调变更。

## 纠正此前的安全判断

此前曾根据“走原版 IL2CPP 字段 API”判断字符串赋值有写屏障、因此安全。这个判断没有核对本机 API 对引用参数的层级，应撤回。实际机器码表明写屏障确实会执行，但它保护的是已经写入的**错误缓冲区地址**；写屏障不能将非托管地址变成 String 对象。

R14 的修正同时满足两点：传入真实托管对象指针，并经专用字段赋值 API 执行原版 GC 写屏障。上述结论来自本机匹配版本 ELF，不是仅凭通用 C 函数签名推断；`void *value` 这个声明本身不足以区分数值缓冲区与对象引用。

## 与其他生命周期调整的关系

- R12 临时 strong GCHandle：补上新 Effect / 返回 List 在 JavaScript 暂存、尚未入托管容器时的 GC 根。它解决保活问题，不会修正 GroupId 内已经写坏的指针。每 case 临时根归零只能证明句柄没有遗留，不能证明字段引用正确。
- R13 禁攻保留原效果：取消原列表里的全部效果，并让原队列负责路由与返池，避免扩展提前 Clear/Return 改变原版所有权。它解决池化时序问题，同样不能修正 Buff 的引用 ABI。
- R14 引用字段修正：避免把原生 buffer 写成托管对象引用。临时根和禁攻所有权调整继续作为独立改进保留。

后续 R14 实机证据：[14 个攻击用例](../06.R19实现与验收记录/工程资料索引.md#ref-d6548fddf8d4) 和 [7 条动作断言](../06.R19实现与验收记录/工程资料索引.md#ref-99f2c9deb5d7) 全部 PASS，包含 fixture Buff 设置、狗头减益和延期扣阳光，连续 14 个攻击测试局截至 generation 14，扩展错误为 0、临时根回到零。此结果由主代理操作设备取得；详细范围及 R15/R16 状态见 [攻击规则验证进展](../02.缓存契约与扩展规则/attack-rules.md)。

这些功能性回归没有单独输出每一次引用赋值后“字段指针等于新建 String 指针、类型名及数字字符串内容”的完整探针，不能伪称这些逐次指针断言已经执行。源码 ABI 证据与真实技能回归分别保留，后续新候选及动画对照仍需要其自己的设备结果。
