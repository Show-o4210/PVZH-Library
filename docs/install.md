# 安装说明

**推荐（玩家）**：直接使用社区精简包  
`share/PVZH_LocalInventory_CommunityPack/`（或同目录 zip）。

当前包版本：**v3c.1**（v3c so + 社区非官方封面）。

步骤与规则见该包内 **`README.md`**。

**公开 Git 源码树**：见 `github_ready/`（不含 APK）。

## 维护者本地产物

| 路径 | 用途 |
|------|------|
| `dist/apk/pvzh_mod_base_v3c.apk` | 最终 APK（v3c.1） |
| `dist/arm64-v8a/libil2cpp.so` | 补丁 so |
| `templates/cache/mod/` | extra 模板 |

重建 so：`python scripts/build_and_patch.py`  
排错：`docs/troubleshooting.md`
