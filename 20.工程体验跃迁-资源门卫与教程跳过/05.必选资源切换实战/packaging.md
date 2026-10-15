# mod2 技能候选包的构建

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/packaging.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../../21.语义调试与技能扩展实战/06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

## 发布范围

`scripts/build_apk.py` 以独立底座 B4 为基准：

```text
D:/Codex2/pvzh-mod/pvzh-base/dist/PVZH_1.67.8_base_b4_11056_arm64.apk
SHA-256 9AF06D613C55644E1BBC9558F0108F0C61E0B37830DA29525D5935C54FEF97BC
```

只允许改变以下有效载荷：

| 范围 | 操作 |
|---|---|
| `classes9.dex` | 完整替换为独立编译的必选资源界面 |
| `lib/arm64-v8a/libpvzhgadget.script.so` | 替换为当前技能和调试源码的编译结果 |
| `assets/mod2_profiles/` | 增加原版、mod2 两组资源及登记清单，共七个文件 |
| `META-INF/*` 和 APK 签名块 | 使用既有本机发布证书重新签名 |

其它文件逐个比较完整解压字节的 SHA-256，出现未经登记的修改、新增或删除即失败。仅允许 7-Zip 添加 `assets/`、`lib/`、`lib/arm64-v8a/` 的空目录记录。已有的 11056 全量资源仍然内置；`libil2cpp.so`、`libunity.so` 和其它原生模块保持原始内容，报告记录其散列。

## 构建顺序

先停止并行源码编辑，确认规则模块和卡牌资源已经准备完毕，再执行：

```powershell
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' android/build_gate.py
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' scripts/build_apk.py --revision r1
```

产物名为 `dist/PVZH_1.67.8_mod2_skills_r1_11056_arm64.apk`，同名 JSON 记录构建证据；`build/r1.script.so` 保存嵌入脚本。每次候选必须使用新 revision，已有 APK、报告或脚本产物均不覆盖。

构建检查 B4 指纹、启动界面 DEX 与源文件一致、无重复类、资源清单中六份 Bundle 的大小和 SHA-256、缓存相对路径、2880 条完整资源索引、ZIP 重复条目、最终脚本与 DEX 的真实 APK 内容、签名和 zipalign。打包前后再次比较源文件、DEX 和资源文件的散列；编辑在构建期间发生时拒绝发布。

证书固定为 `845924FF7FE54B5C428E74DA8FE5CF8F61D7E7DB5205D003AB517C5BC07992D3`。凭证只从既有本机 `private/release-signing` 位置读取，并通过子进程临时环境变量交给 apksigner，不复制进本项目或打印到日志。

构建报告中的 `runtime: NOT TESTED` 只表示尚未实机验证，不能据此声称技能已通过。打包脚本不会安装 APK、清除账号或连接 ADB。

## 调试连接的资源选择

`scripts/session.py` 保持原有调用参数兼容，末尾增加 `profile`：

```python
from session import launch, start_fixture
launch(reset=True, profile='mod2')
start_fixture({'sun': 50}, reset=True, profile='original')
```

冷启动默认为 `mod2`。脚本先强行停止旧进程，再通过启动界面的显式 Intent 参数请求原生选择按钮；准备、备份、资源校验和选择记录仍走真实界面流程。它不会直接启动 NimbleActivity 绕过资源切换。

`launch(reset=False)` 若已连接到活动的 Gadget，仅等待原有进程的 `installed` 和 `app_ready`，不再打开资源界面，也不切换正在使用的 profile。没有活动接口时才进行冷启动选择。需要确保切换原版 / mod2 时，应明确使用 `reset=True`；该操作会结束当前测试局。

接口的 `variant` 继续为 `pvzh-test-mode`，兼容原验收脚本。资源界面与事务恢复细节见 [resource-selector.md](resource-selector.md)。
