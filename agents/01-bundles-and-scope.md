# 01 · Bundle 读写与修改边界

## 先做什么

1. 检查用户输入、适用 AGENTS.md、Git 状态、已有 Python/UnityPy/ADB。找到可用工具就停止寻找替代品。
2. 枚举 UnityPy 对象，记录对象类型、`path_id`、`m_Name`。不要把 Bundle 文件名当成内部资产名。
3. 解包后再决定修改对象；输出到独立目录，原包不覆盖。

本次实际对应：

| Bundle | 目标类型 | m_Name | path_id |
|---|---|---|---|
| card_data_1 | TextAsset | cards | -79917718294181953 |
| data_assets_29 | TextAsset | PVE_Soft_Node_Zombie_200 | 4397490390251977300 |
| cn_8 | TextAsset | LocalizedStrings | -2978648870419362077 |

## 最小 UnityPy 模式

```python
import UnityPy
env = UnityPy.load(str(input_path))
matches = []
for obj in env.objects:
    if obj.type.name != "TextAsset":
        continue
    tree = obj.read_typetree()
    if tree["m_Name"] == expected_name:
        matches.append((obj, tree))
assert len(matches) == 1
obj, tree = matches[0]
raw = tree["m_Script"]
text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
# 在此解析、深拷贝、精准修改。
tree["m_Script"] = new_text.encode("utf-8") if isinstance(raw, bytes) else new_text
obj.save_typetree(tree)
output_path.write_bytes(env.file.save(packer="lz4"))
```

这里处理的是文本。二进制 TextAsset 的 surrogateescape 规则见音频章节，不应直接套用文本 JSON 流程。

## 必须做的验证

- 重开输出 Bundle，重新解析目标 TextAsset，核对写入值。
- 以 `(serialized_file_name, path_id)` 对齐输入输出对象，比较 `get_raw_data()`。本次每个 Bundle 应当恰好只改变一个 TextAsset 对象；对象数量、其余对象原始字节不变。
- 卡牌逐张比较：先列清本次允许改变的GUID、字段与新增定义。全单位冬青移植案例要求撤去追加技能后原卡与输入相等、非Fighter不变、冬青不重复追加；单卡重写及锦囊改版则验证指定范围，不能把该案例条件套成所有Mod的限制。
- 关卡撤去本次改变的字段后，应与原关卡相等。
- 中文文本的非目标记录顺序、值与空记录不变；新增 Key 唯一、对话引用全部可解析。
- 记录输入输出哈希和 UnityPy 版本。压缩改变造成的包大小变化不代表资源缺失，必须靠回读及对象校验判断。

不要对 JSON 全局替换阵营字符串，不要“清洗”整份文本的引号或标点；只修改明确定位的结构。

可直接运行的完整流程见 [08基础示例](08-basic-mod-walkthrough.md)。GUI编辑器适合人工编辑，但其兼容嗅探／清洗代码不等于精确增量写入；Agent构建应按唯一m_Name定位并验证非目标对象原始字节。
