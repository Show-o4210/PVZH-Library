# 必选资源界面与原版 / mod2 切换

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/resource-selector.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../../21.语义调试与技能扩展实战/06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

## 当前实现

`android/java/com/pvzh/sharecode/ResourceGateActivityV2.java` 替换 B4 已有启动界面，不依赖 Gadget 的 Java bridge。

1. 启动后恢复本工程未完成的资源事务。
2. 调用原有 `FullResourceEngine` 准备内置的 11056 全量资源。原有按资源族名称复用缓存、保留较新官方清单的规则不变。
3. 校验 `assets/mod2_profiles/manifest.json`，启用“原版游戏”和“mod2 改版游戏”两个按钮。
4. 用户明确选择后，校验、暂存、备份并替换登记的三个 Bundle。
5. 写入已校验的选择记录，才启动 `com.ea.nimble.plugin.NimbleActivity`。

界面没有“下次跳过”选项，也不读取旧的跳过偏好。返回键不能启动游戏。资源准备、资源散列校验或写入失败时，停留在界面并提供重试。

## 资源契约

APK 必须包含以下资源：

```text
assets/mod2_profiles/manifest.json
assets/mod2_profiles/original/card_data_1
assets/mod2_profiles/original/data_assets_29
assets/mod2_profiles/original/cn_8
assets/mod2_profiles/mod2/card_data_1
assets/mod2_profiles/mod2/data_assets_29
assets/mod2_profiles/mod2/cn_8
```

清单版本固定为 `schema = 1`，`profiles.original.files` 和 `profiles.mod2.files` 各包含三个键。每条记录要求 `size`、`sha256`、`cache_relative`。可附加标题等元数据，界面不以元数据改变写入路径。

| 文件键 | 固定 `cache_relative` |
|---|---|
| `card_data_1` | `cards/card_data_1` |
| `data_assets_29` | `data_assets_29` |
| `cn_8` | `loc/cn_8` |

上述相对路径位于 `Context.getExternalFilesDir(null)/cache/bundles/files/`。路径、数量、大小和 SHA-256 格式必须符合契约，不能通过清单写入账户文件。

## 选择记录与运行时规则开关

选择完成后原子写入：

```text
/sdcard/Android/data/com.ea.gp.pvzheroes/files/cache/mod2/profile.json
```

示例结构：

```json
{
  "schema": 1,
  "profile": "mod2",
  "manifest_sha256": "所用清单的 SHA-256",
  "selected_at_ms": 0,
  "transaction_id": "本次事务编号",
  "files": {
    "card_data_1": {"path": "cards/card_data_1", "size": 1, "sha256": "已校验的 SHA-256"},
    "data_assets_29": {"path": "data_assets_29", "size": 1, "sha256": "已校验的 SHA-256"},
    "cn_8": {"path": "loc/cn_8", "size": 1, "sha256": "已校验的 SHA-256"}
  }
}
```

散列为小写十六进制。原版 / mod2 的规则扩展应在加载原生模块前读取这个记录；不能只以“安装了改版 APK”判断是否启用新规则。

## 事务、备份与恢复

`Mod2ProfileEngine` 只管理上述三个 Bundle 和 `cache/mod2/` 内的自身文件，不清除账号、卡组、其它 Bundle 或官方清单。

- 三个新文件全部暂存并通过散列校验后才改变正在使用的文件。
- 旧文件备份到 `cache/mod2/backups/<旧 SHA-256>/<文件键>`，按内容复用，不覆盖或清理既有备份。
- 写入 `cache/mod2/transaction.json` 后，以同目录 `Os.rename` 分别原子替换文件。三个文件全部重新校验后，最后原子写入 `profile.json`。
- 如果替换中失败，恢复三个旧文件与之前的选择记录，保持 Unity 未启动。
- 如果进程在事务中结束，下次准备时恢复旧文件；若选择记录与三个新文件已完整提交，只清理已完成的事务记录。

每个文件替换是原子的，三个文件合在一起通过事务记录恢复；Unity 在全部提交前始终被阻止启动。

## 冷启动限制

如果同一进程已经加载 `libil2cpp.so`，旧卡牌定义可能仍在内存里。此时界面显示“游戏仍在后台运行，请强行停止后重新打开”，禁止资源切换。

初版只支持可靠的冷启动选择，不宣称可以在活动对局中热切换。测试前必须 `am force-stop`。从最近任务移除若未终止进程，仍需系统“强行停止”。需要无缝热切换时，应另行设计独立启动进程和游戏进程重启，不应只换文件后复用旧 Unity。

## 无坐标点击的显式测试选择

仅在 Intent 显式同时提供 `pvzh_test_select=true` 和合法的 `pvzh_test_profile` 时，准备完成后调用相应原生按钮的 `performClick()`。这个请求写入 `PVZH-MOD2-GATE` 日志并移除 Intent 参数，不读取持久化自动选择偏好。普通启动仍要求用户选择。

```powershell
$adb = 'F:\Tools\.env\platform-tools\adb.exe'
& $adb -s 1B271FDF60B7UU shell am force-stop com.ea.gp.pvzheroes
& $adb -s 1B271FDF60B7UU shell am start -n com.ea.gp.pvzheroes/com.pvzh.sharecode.ResourceGateActivityV2 --ez pvzh_test_select true --es pvzh_test_profile mod2
```

`original` 使用同一命令，只更换最后的值。原生按钮的 content-description 分别为 `profile_original`、`profile_mod2`、`profile_retry`，可用 UI XML 确认按钮存在及状态，无需截图。

## 构建与验收范围

```powershell
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' android/build_gate.py
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' android/verify_profile_engine.py
```

构建使用现有 Android SDK 36、D8 36.0.0 和 JDK。产物 `android/build/classes9.dex` 是完整替换，不是追加 DEX。B4 的旧 `classes9.dex` 只有旧启动界面与 `FullResourceEngine`；构建脚本会核对该范围，并检查新 DEX 与其余八份 DEX 不存在同名类。`FullResourceEngine.java` 按原工作区源码原样复制。测试专用 I/O / JSON stub 永远不进入 APK。

不需要更改 B4 的 AndroidManifest，已经登记的 `ResourceGateActivityV2` 继续作为 Launcher。APK 集成时仅替换 `classes9.dex`，添加资源配置，并替换本次 Gadget 脚本；原有 `classes.dex` 至 `classes8.dex` 保留。

本代理已完成编译和 11 项桌面事务测试：原版 / mod2 切换、旧文件备份、损坏素材拒绝、发布中失败回滚、进程中断恢复、已提交事务恢复、非法路径拒绝、账户文件保持不变。`android/build/profile-engine-tests.json` 保存结果。桌面测试不证明 Android 实机 UI 与存储权限，实际 APK 安装及设备切换由主代理统一验收。
