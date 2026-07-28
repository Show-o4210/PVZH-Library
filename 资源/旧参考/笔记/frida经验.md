# Frida 无法抓到游戏 so 的排查记录（x86_64 模拟器 + ARM64 游戏）

## 问题现象

环境中：

* Windows
* 安卓模拟器（Android 9）
* x86_64 架构
* 已安装 Frida
* frida-server 正常运行

现象：

```bash
frida-ps -U
```

可以识别游戏进程。

但是：

```js
Process.enumerateModules()
```

无法看到：

```text
libil2cpp.so
libunity.so
```

等游戏核心 so。

---

# 一、最开始的问题：ADB offline

初始状态：

```bash
adb devices
```

显示：

```text
127.0.0.1:21503 offline
```

导致：

```bash
adb shell
```

无法使用。

---

## 解决方法

执行：

```bash
adb kill-server
taskkill /f /im adb.exe
adb start-server
adb connect 127.0.0.1:21503
```

确认：

```bash
adb devices
```

变成：

```text
127.0.0.1:21503 device
```

---

# 二、确认模拟器环境

确认 CPU 架构：

```bash
adb shell getprop ro.product.cpu.abi
```

输出：

```text
x86_64
```

确认内核：

```bash
adb shell uname -m
```

输出：

```text
x86_64
```

确认 Root：

```bash
adb shell id
```

输出：

```text
uid=0(root)
```

说明：

* Root 正常
* ADB 正常
* 模拟器是 x86_64 环境

---

# 三、确认 Frida 正常

检查 frida-server：

```bash
adb shell ps -A | grep frida
```

成功看到：

```text
frida
```

确认版本：

```bash
adb shell /data/local/tmp/frida --version
```

输出：

```text
17.8.2
```

PC 端：

```bash
frida-ps -U
```

成功列出进程。

说明：

* frida-server 正常
* Frida attach 正常
* Python/frida 版本无问题

---

# 四、确认游戏进程

获取当前 Activity：

```bash
adb shell dumpsys window | findstr mCurrentFocus
```

输出：

```text
com.ea.gp.pvzheroes/com.ea.nimble.plugin.NimbleActivity
```

确认游戏进程：

```bash
adb shell ps -A | findstr com.ea.gp.pvzheroes
```

得到 PID。

---

# 五、问题核心：枚举不到游戏 so

进入 Frida：

```bash
frida -U -n com.ea.gp.pvzheroes
```

执行：

```js
Process.enumerateModules().map(m => m.name)
```

结果：

* 能看到系统 so
* 能看到 libhoudini.so
* 看不到 libil2cpp.so

---

# 六、最终定位问题

检查 APK lib 目录：

```bash
adb shell ls -R /data/app/xxx/lib
```

发现：

```text
lib/arm64/
```

游戏实际只有：

```text
arm64-v8a/libil2cpp.so
```

而模拟器环境是：

```text
x86_64
```

---

# 七、根本原因

这是：

# “x86 模拟器 + ARM 游戏 + Houdini 转译”

导致的问题。

逍遥模拟器会通过：

```text
libhoudini.so
```

将 ARM64 so 转译运行。

因此：

* 游戏可以运行
* ARM so 可以执行
* 但 Frida 无法正常枚举 ARM native module

所以：

```js
Process.enumerateModules()
```

无法看到：

```text
libil2cpp.so
```

---

# 八、重要结论

## 这不是：

* Frida 安装错误
* Python 版本问题
* frida-server 问题
* Root 权限问题
* hook 写错

而是：

# ABI / 架构不匹配问题

---

# 九、这种环境下能做什么

## 可以：

### 1. Java 层 Hook

例如：

```js
Java.perform(...)
```

### 2. 静态分析

提取：

```text
libil2cpp.so
global-metadata.dat
```

使用：

* Il2CppDumper
* Cpp2IL
* IDA
* Ghidra

### 3. 部分内存修改

部分 CE 类方案仍可用。

---

# 十、这种环境下不能稳定做什么

## ❌ Native so Hook

例如：

```js
Module.findBaseAddress("libil2cpp.so")
```

会失败。

或者：

```js
Interceptor.attach(...)
```

无法定位目标。

---

# 十一、推荐解决方案

## 最推荐：换 ARM64 环境

例如：

* ARM64 安卓模拟器
* Android Studio ARM Emulator
* ARM 真机

然后使用：

```text
frida-server-android-arm64
```

这样：

```js
Process.enumerateModules()
```

即可正常看到：

```text
libil2cpp.so
libunity.so
```

native hook 才能正常工作。

---

# 十二、本次排查最终结论

本次问题已经完整定位：

✅ adb 正常
✅ root 正常
✅ frida-server 正常
✅ attach 正常
✅ 游戏进程正常

最终卡点：

```text
x86_64 模拟器运行 arm64-v8a 游戏
```

属于：

# Frida 与 Houdini ARM 转译层兼容问题。
