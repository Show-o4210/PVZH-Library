# 必选资源界面的实机验收

> 文档归档：2026-10-15；来源 `mod2-runtime/docs/gate-acceptance.md`。原工程文档保留，本文为按主题归类、修正链接的快照。
> “当前／待验收／手机状态”均指原记录当时；本次归档不重新操作设备。库外源码、APK与原始日志见[工程引用说明](../../21.语义调试与技能扩展实战/06.R19实现与验收记录/工程资料索引.md)，所收检查摘要不替代完整原始证据。

脚本：`tests/verify_mod2_gate.py`。**默认只输出计划，不操作设备、不创建证据文件。** 只有传入 `--run` 才执行。它不安装 APK，不清除应用数据，也不读取账户凭证。

## 检查步骤

1. 停止旧游戏进程，读取已登记的选择记录与三个 Bundle 散列，记录测试前状态。
2. 使用正常 Launcher 启动，不提供测试自动选择参数。
3. 通过 `uiautomator dump` 的 XML 检查原版 / mod2 两个原生按钮存在且启用，界面没有跳过复选框。
4. 检查前台 Activity 仍是资源界面，进程没有加载 `libil2cpp.so`；已有选择记录与已经存在的三个 Bundle 未因正常启动而改变。
5. 发送系统 Back，再检查资源界面、原生按钮和 Unity 未加载状态，证明返回键不能进入游戏。
6. 分别冷启动选择 `original → mod2 → original`，每轮均核对 `status.resource_profile`、`app_ready`、`profile.json` 和三个真实缓存文件的 SHA-256，必须共同符合 APK 资源清单。

Android 没有可跨版本使用的 `am back` 子命令，脚本使用 `adb shell input keyevent KEYCODE_BACK` 发送系统返回操作，再用 Activity 状态和 XML 验证结果。测试没有截图、触摸坐标或模拟卡牌点击。

默认最后停在原版模式。传入 `--final-profile mod2` 会增加一轮改版冷启动并完整验证，便于主代理继续技能测试。冷启动会结束当前对局；这个结果不代表测试了游戏内部的新技能。

## 调用

从 `mod2-runtime` 目录执行：

```powershell
# 只读本地计划，不接触设备
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' tests/verify_mod2_gate.py

# 主代理确认候选已安装后才实际执行
& 'C:\Users\15731\AppData\Local\Python\pythoncore-3.14-64\python.exe' tests/verify_mod2_gate.py --run --name r1-gate-acceptance --final-profile mod2
```

使用现有 `scripts/device.py` 的 Pixel 6 序列号和 `scripts/session.py` 的显式资源界面选择流程；`--port` 可改本地主机的转发端口。ADB 普通 shell 无法读取文件时，只为已登记的缓存或当前包 `/proc/<pid>/maps` 使用 root 读取，不修改权限。

## 证据与边界

执行时在 `evidence/<name>/` 创建独立目录，不覆盖旧记录。保存正常启动、返回之后的 UI XML，每轮选择的状态 / 资源散列 / 收据，以及最终 `result.json`。失败同样保留已经完成的步骤和错误。

首次缺少完整资源时，正常准备可能从 APK 补齐缺失 Bundle，因此“无选择不改文件”只针对此前已经存在的文件；选择记录始终不允许提前提交。脚本不删除账户、其它缓存、备份或测试证据。

如果前台已有 Unity 而直接重开界面，初版应阻止切换并提示冷启动。此脚本每轮主动停止旧进程，验证的是受支持的冷启动模式，不宣称支持活动对局热切换。

脚本尚未由子代理执行设备操作；是否安装和实际运行由主代理统一决定。未带 `--run` 的本地计划与 XML 解析检查不能当成实机通过证据。

## 最终 R19 交付

主代理已运行 `tests/verify_release_handoff.py --revision r19 --name r19-release-handoff --run`，[实际报告](../../21.语义调试与技能扩展实战/06.R19实现与验收记录/工程资料索引.md#ref-6c187082f9ad) 8项全部PASS。核对当前已安装APK与主机R19逐字节SHA-256、内嵌脚本/DEX/Rev4清单及六份资源、原版收据与三份真实缓存、正常Launcher双按钮/无跳过、Back后仍未加载Unity且资源不变，再显式选择mod2核对新收据与三份缓存。完整原版游戏回归在此前同一R19完成，见[17项及整局报告](../../21.语义调试与技能扩展实战/06.R19实现与验收记录/工程资料索引.md#ref-a23302579545)。

最终使用无测试extra的正常冷启动，手机停在必选界面等待用户选择；两按钮均可用，Unity与libil2cpp尚未加载。最后已验证的磁盘缓存为mod2，此时正常打开界面没有再次更改文件，用户可以自由选原版或改版。全程无清除账号、截图或卡牌坐标点击；Back仍采用系统返回键。此交付检查使用既有Gate代码，不把选择界面通过扩大为全部技能或初始牌组建局通过。
