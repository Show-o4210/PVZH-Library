# PVZH Local Inventory Mod Base

全静态方案：在**本地模式**下合并 `inventory_extra.json`，让社区自定义卡可拥有。  
无需 Frida 常驻。

| | |
|--|--|
| 机制 | 静态补丁 `libil2cpp.so`（**v3c**），`SetLocalPlayerInventory` 后 merge |
| 创作 | `files/cache/mod/inventory_extra.json` + `card_data` 缓存 |
| 当前补丁 | v3c（真机 bionic `.dynamic` 偏移已对齐） |
| 社区玩家包 | **不在本 Git 树内**（含 APK，请用本地 `share/` 分发） |

## 本仓库包含什么

本目录（`github_ready/`）是**适合公开 GitHub 的源码与文档树**：

- 文档、脚本、模板、原生参考实现  
- 补丁元数据（`PATCH_INFO`、payload 反汇编/字节）  
- **不包含**：游戏 APK、原版/补丁 `libil2cpp.so` 二进制、IL2CPP dump、Unity 资源、社区安装包  

完整工作区与社区 zip 在作者本地仓库根目录；范围说明见 [`GITHUB_SCOPE.md`](./GITHUB_SCOPE.md)。

## 快速入口

| 角色 | 入口 |
|------|------|
| 卡师 | [`docs/modder_guide.md`](./docs/modder_guide.md) |
| 全流程 + 错误档案 | [`docs/workflow_and_experience.md`](./docs/workflow_and_experience.md) |
| 按现象排错 | [`docs/troubleshooting.md`](./docs/troubleshooting.md) |
| 精简经验 | [`docs/lessons_learned.md`](./docs/lessons_learned.md) |
| 重建 so | `python scripts/build_and_patch.py`（需自备合法取得的原版 so） |

## 目录

```text
docs/           完整文档
scripts/        构建 / 克隆卡 / 校验
templates/      inventory_extra 模板
examples/       JSON 示例（无游戏 card_data 二进制）
native/         merge 语义 C 参考
dist/
  arm64-v8a/    PATCH_INFO + payload 元数据（无 so）
  card_mods/    说明与 empty extra
```

## 自行构建补丁 so（维护者）

1. 将与目标游戏版本匹配的 `libil2cpp.so` 放到工作区 `reference/il2cpp/`（**勿提交**）。  
2. `pip install -r requirements.txt`  
3. `python scripts/build_and_patch.py`  
4. 产物：`dist/arm64-v8a/libil2cpp.so`（本地使用 / 打进自有 APK，勿默认公开上传）

真机请使用 **v3c** 策略（旧 v3b 会因 `.dynamic` 与 `PT_DYNAMIC` 偏移不一致白屏）。

## 约束

- 仅本地 / 单机研究；勿在官方 PvP 使用未收录卡。  
- so 与游戏版本绑定（见 `dist/arm64-v8a/PATCH_INFO.txt`）。  
- 玩家向安装包请使用作者分发的 **Community Pack（v3c.1）**，不在本 Git 树。

## 许可

本项目**原创**的脚本、原生参考代码与文档采用 [MIT License](./LICENSE)。

MIT **不适用于** Plants vs. Zombies Heroes 游戏程序、APK、素材、反编译产物、dump、商标及其他第三方内容；权利归各自权利人所有。  
本项目与 EA、PopCap、Glu 无关联，也未获得其认可或赞助。

## 支持项目

本项目免费提供，仅用于本地研究与社区创作。若工具和文档帮到你，可自愿赞赏作者。

赞赏不代表购买游戏内容，不解锁功能，也不构成付费支持或更新承诺。

<p align="center">
  <img src="./docs/assets/support.png" alt="赞赏码" width="360">
</p>
