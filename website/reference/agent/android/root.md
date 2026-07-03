# Root 检测绕过 `agent/src/android/root.ts`

在目标 Android 进程内拦截各类 root 检测实现，按调用方期望的方向返回“已 root”或“未 root”的结果。模块导出 `disable()` 与 `enable()` 两个 RPC：前者让检测返回“未 root”，后者让检测返回“已 root”，用于反向验证检测点是否被覆盖。两条 RPC 各注册一个 Job（`root-detection-disable` / `root-detection-enable`）。

## 📋 模块概览

| 项目 | 值 |
| --- | --- |
| 源码路径 | `agent/src/android/root.ts` |
| 平台 | Android（Java 层） |
| 导出的 RPC | `disable`（`agent/src/rpc/android.ts:90` → `androidRootDetectionDisable`）、`enable`（`agent/src/rpc/android.ts:91` → `androidRootDetectionEnable`） |
| 依赖 | `../lib/jobs.js`、`../lib/color.js`、`./lib/libjava.js`、`./lib/types.js` |

## 🎯 解决的问题

- 应用通过 `Build.TAGS.contains("test-keys")` 判断是否运行在测试签名固件。
- 应用调用 `Runtime.exec("su")` 或检查 `java.io.File.exists()` 判断 `/system/xbin/su` 等 su 路径是否存在。
- 集成了 [RootBeer](https://github.com/scottyab/rootbeer) 库的应用通过 `isRooted()`、`checkForBinary()`、`RootBeerNative.checkForRoot()` 等多个方法交叉验证。
- 集成了 [JailMonkey](https://github.com/GantzyLabs/jail-monkey) 的 RN 应用通过 `JailMonkeyModule.getConstants()` 一次性返回 `isJailBroken` 等多个布尔标志。

## 🏗️ 导出的 RPC 方法

| RPC 名 | 说明 |
| --- | --- |
| `disable()` | 让全部 13 条检测返回“未 root”，注册为 `root-detection-disable` Job |
| `enable()` | 让 4 条基础检测 + RootBeer 大部分检测返回“已 root”，用于验证覆盖完整性 |

### `rpc.disable` — 让检测返回“未 root”

源码：`agent/src/android/root.ts:430`

`disable()` 对每个 helper 传入 `success=false`，表示“把检测结果标记为未 root”。所有 helper 在 `Java.perform` 内替换方法实现；RootBeer/JailMonkey 相关类不存在时返回 `null`，由 `Job.addImplementation` 跳过。

```ts
export const disable = async (): Promise<void> => {
  const job: jobs.Job = new jobs.Job(jobs.identifier(), 'root-detection-disable');
  job.addImplementation(await testKeysCheck(false, job.identifier));
  job.addImplementation(await execSuCheck(false, job.identifier));
  job.addImplementation(await fileExistsCheck(false, job.identifier));
  job.addImplementation(await jailMonkeyBypass(false, job.identifier));
  job.addImplementation(await rootBeerIsRooted(false, job.identifier));
  // ... 其余 RootBeer helper 同样传 false
  jobs.add(job);
};
```

### `rpc.enable` — 让检测返回“已 root”

源码：`agent/src/android/root.ts:450`

`enable()` 用于反向验证：把检测结果强制为“已 root”，观察 App 是否因此触发额外行为，从而确认对应检测点已被 Hook 覆盖。注意 `rootBeerCheckSeLinux` 在 enable 分支里仍传 `false`（源码 `agent/src/root.ts` 第 466 行），与 disable 一致。

### 关键 helper：`testKeysCheck`

源码：`agent/src/android/root.ts:30`

不直接 Hook `Build.TAGS`，而是 Hook `java.lang.String.contains`，仅在参数为 `"test-keys"` 时返回伪造结果，其余字符串走原实现，避免误伤业务逻辑。

```ts
JavaString.contains.implementation = function (name) {
  if (name !== "test-keys") { return this.contains.call(this, name); }
  if (success) { return true; }
  return false;
};
```

### 关键 helper：`execSuCheck`

源码：`agent/src/android/root.ts:52`

Hook `Runtime.exec(String)`，当命令以 `"su"` 结尾时：`success=true` 放行原调用，`success=false` 抛 `java.io.IOException("objection anti-root")`。

### 关键 helper：`fileExistsCheck`

源码：`agent/src/android/root.ts:77`

Hook `java.io.File.exists()`，对 `commonPaths` 列表中的 13 条 su 路径返回伪造值，其余路径走原实现。`commonPaths` 定义在 `agent/src/android/root.ts:14`。

### 关键 helper：`jailMonkeyBypass`

源码：`agent/src/android/root.ts:378`

Hook `com.gantix.JailMonkey.JailMonkeyModule.getConstants()`，返回一个 `java.util.HashMap`，对 `isJailBroken`、`hookDetected`、`canMockLocation`、`isOnExternalStorage`、`AdbEnabled` 五个键统一填 `Boolean.TRUE` 或 `Boolean.FALSE`。

```ts
const JavaFalseObject = JavaBoolean.FALSE.value;
JavaJailMonkeyModule.getConstants.implementation = function () {
  const hm = JavaHashMap.$new();
  hm.put("isJailBroken", JavaFalseObject);
  hm.put("hookDetected", JavaFalseObject);
  // ...
  return hm;
};
```

### RootBeer 系列 helper

| helper | 目标方法 | 位置 |
| --- | --- | --- |
| `rootBeerIsRooted` | `RootBeer.isRooted()` | `agent/src/android/root.ts:108` |
| `rootBeerCheckForBinary` | `RootBeer.checkForBinary(String)` | `agent/src/android/root.ts:143` |
| `rootBeerCheckForDangerousProps` | `RootBeer.checkForDangerousProps()` | `agent/src/android/root.ts:176` |
| `rootBeerDetectRootCloakingApps` | `RootBeer.detectRootCloakingApps()` | `agent/src/android/root.ts:209` |
| `rootBeerCheckSuExists` | `RootBeer.checkSuExists()` | `agent/src/android/root.ts:244` |
| `rootBeerDetectTestKeys` | `RootBeer.detectTestKeys()` | `agent/src/android/root.ts:277` |
| `rootBeerCheckSeLinux` | `com.scottyab.rootbeer.util.isSelinuxFlagInEnabled()` | `agent/src/android/root.ts:310` |
| `rootBeerNative` | `RootBeerNative.checkForRoot([Ljava.lang.Object;)` | `agent/src/android/root.ts:343` |

```mermaid
flowchart TD
    A[disable/enable] --> B{success 标志}
    B -->|false| D[检测返回 未 root]
    B -->|true| E[检测返回 已 root]
    A --> F[Java.perform 内逐个 await helper]
    F --> H1[testKeysCheck: String.contains]
    F --> H2[execSuCheck: Runtime.exec]
    F --> H3[fileExistsCheck: File.exists]
    F --> H4[jailMonkeyBypass: JailMonkeyModule.getConstants]
    F --> H5[RootBeer 8 个方法]
    H1 & H2 & H3 & H4 & H5 --> G[Job.addImplementation 仅在非 null 时挂载]
    G --> J[jobs.add 注册 root-detection-{disable,enable}]
```

## ⚙️ 实现要点

- **`success` 双向标志**：同一套 helper 通过布尔参数切换“伪造为真/伪造为假”，`enable` 分支可用来探测 App 对“检测到 root”后的反应，定位隐藏的检测点。
- **类不存在即跳过**：RootBeer/JailMonkey 的 helper 用 `try/catch` 捕获 `ClassNotFoundException`，返回 `null` 后由 `Job.addImplementation` 跳过。
- **窄范围 Hook**：`testKeysCheck` 只在参数为 `"test-keys"` 时介入，`fileExistsCheck` 只对 `commonPaths` 列表内的路径介入，最大限度减少对业务逻辑的副作用。
- **Native 层覆盖**：`rootBeerNative` 处理 RootBeer 调用 native 库的 `RootBeerNative.checkForRoot`，返回 `1`/`0` 表示伪造结果。
- **异步消息**：每次 Hook 命中走 `send()` 带 `[ident]` 前缀的提示，便于在控制台追踪哪个检测被触发。

## 🔍 源码索引

| 符号 | 位置 |
| --- | --- |
| `commonPaths` | `agent/src/android/root.ts:14` |
| `testKeysCheck` | `agent/src/android/root.ts:30` |
| `execSuCheck` | `agent/src/android/root.ts:52` |
| `fileExistsCheck` | `agent/src/android/root.ts:77` |
| `rootBeerIsRooted` | `agent/src/android/root.ts:108` |
| `rootBeerCheckForBinary` | `agent/src/android/root.ts:143` |
| `rootBeerCheckForDangerousProps` | `agent/src/android/root.ts:176` |
| `rootBeerDetectRootCloakingApps` | `agent/src/android/root.ts:209` |
| `rootBeerCheckSuExists` | `agent/src/android/root.ts:244` |
| `rootBeerDetectTestKeys` | `agent/src/android/root.ts:277` |
| `rootBeerCheckSeLinux` | `agent/src/android/root.ts:310` |
| `rootBeerNative` | `agent/src/android/root.ts:343` |
| `jailMonkeyBypass` | `agent/src/android/root.ts:378` |
| `export const disable` | `agent/src/android/root.ts:430` |
| `export const enable` | `agent/src/android/root.ts:450` |

## 🔗 相关文档

- [Frida 与 Agent](/guide/frida-agent)
- [RPC 通信机制](/guide/rpc)
- [Android 命令：Root 检测绕过](/reference/commands/android/root)
- [Agent Job 调度](/reference/agent/lib/jobs)
