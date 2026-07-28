# GitHub 上传范围

本目录是从完整工作区抽出的**可公开上传**树，方便直接 `git init` / 推送到 GitHub。

## 建议上传（已放入本目录）

| 内容 | 说明 |
|------|------|
| `docs/` | 架构、补丁、排错、卡师指南、错误档案 |
| `scripts/` | 构建 payload、打 so 补丁、克隆卡、校验 JSON |
| `native/` | merge 语义 C 参考 |
| `templates/` | `inventory_extra` 模板 |
| `examples/` | 仅 JSON / Markdown 示例 |
| `dist/arm64-v8a/PATCH_INFO.txt` 等元数据 | 锚点与策略说明 |
| `dist/arm64-v8a/payload*.{bin,S}` | 小体积 payload，便于对照 |
| `LICENSE` / `README.md` / `PLAN.md` / `requirements.txt` | 工程信息 |

## 不要上传（保留在完整工作区）

| 路径（完整工作区） | 原因 |
|--------------------|------|
| `apk/1.apk` | 完整游戏安装包 |
| `dist/apk/*.apk`、`share/**/*.apk`、`share/*.zip` | 含游戏程序的改包 / 社区安装包 |
| `dist/arm64-v8a/libil2cpp.so` | 修改后的游戏原生库 |
| `reference/il2cpp/*` | dump、metadata、原版 so |
| `reference/samples/*` 中的大数据 | 游戏导出数据 |
| `examples/**/card_data_*`、`dist/card_mods/card_data_*` | UnityFS / 游戏卡表二进制 |
| `_tmp_*` | 本地临时与备份 |

玩家向产物请走本地 **`share/PVZH_LocalInventory_CommunityPack/`**（或 zip），用网盘/群文件分发，而不是放进公开 Git 默认分支。

## 推荐上传步骤

```bash
cd github_ready
git init
git add .
git status   # 确认无 .apk / .so / dump
git commit -m "Initial public source: PVZH local inventory mod base (v3c docs+scripts)"
# gh repo create ... 或 git remote add origin ...
git push -u origin main
```

若要把补丁 so 提供给协作者：使用 **GitHub Releases 私有草稿**、网盘或仅社区包，并自行评估版权风险；默认不进 git 历史。

## 与完整工作区的关系

```text
PVZH_LocalInventoryMod/          ← 完整本地工作区（含 APK、so、dump）
  share/                         ← 社区分享包（玩家）
  github_ready/                  ← 本树：准备 git push
  docs/ scripts/ ...             ← 源与 github_ready 同步维护
```

更新文档或脚本后：改完整工作区对应文件，再同步复制到 `github_ready/`（或只在一侧改并复制）。
