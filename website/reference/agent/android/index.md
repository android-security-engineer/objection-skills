# 🤖 Agent · Android 实现

`agent/src/android/` 下每个 `.ts` 文件实现一组在 **Android 目标进程内**运行的逻辑，通过 `rpc.exports` 暴露给 Python 侧。所有 Java 交互经 `lib/libjava.ts` 的 `wrapJavaPerform` Promise 化包装。

## 📂 文件清单

### 主模块

| 文档 | 源码 | 主要 RPC |
| --- | --- | --- |
| [clipboard](/reference/agent/android/clipboard) | `android/clipboard.ts` | `androidClipboardMonitor` |
| [filesystem](/reference/agent/android/filesystem) | `android/filesystem.ts` | `androidFile*` |
| [general](/reference/agent/android/general) | `android/general.ts` | `androidDeoptimize` / `androidShellExec` |
| [heap](/reference/agent/android/heap) | `android/heap.ts` | `androidHeap*` |
| [hooking](/reference/agent/android/hooking) | `android/hooking.ts` | `androidHooking*` |
| [intent](/reference/agent/android/intent) | `android/intent.ts` | `androidIntent*` |
| [keystore](/reference/agent/android/keystore) | `android/keystore.ts` | `androidKeystore*` |
| [monitor](/reference/agent/android/monitor) | `android/monitor.ts` | `androidMonitor*` |
| [pinning](/reference/agent/android/pinning) | `android/pinning.ts` | `androidSslPinningDisable` |
| [proxy](/reference/agent/android/proxy) | `android/proxy.ts` | `androidProxySet` |
| [root](/reference/agent/android/root) | `android/root.ts` | `androidRootDetection*` |
| [shell](/reference/agent/android/shell) | `android/shell.ts` | `androidShellExec` |
| [userinterface](/reference/agent/android/userinterface) | `android/userinterface.ts` | `androidUi*` |

### lib 工具模块

| 文档 | 源码 | 作用 |
| --- | --- | --- |
| [lib/intent-utils](/reference/agent/android/lib/intent-utils) | `android/lib/intentUtils.ts` | Intent 分析 |
| [lib/interfaces](/reference/agent/android/lib/interfaces) | `android/lib/interfaces.ts` | TypeScript 接口定义 |
| [lib/libjava](/reference/agent/android/lib/libjava) | `android/lib/libjava.ts` | Java 桥兼容层 |
| [lib/types](/reference/agent/android/lib/types) | `android/lib/types.ts` | Java 类别名 |

## 🔗 相关文档

- [Agent 总览](/reference/agent/)
- [rpc/android 聚合](/reference/agent/rpc/android)
- [Frida 与 Agent](/guide/frida-agent)
