# 🍎 Agent · iOS 实现

`agent/src/ios/` 下每个 `.ts` 文件实现一组在 **iOS 目标进程内**运行的逻辑，通过 `rpc.exports` 暴露给 Python 侧。所有 ObjC 交互经 `lib/libobjc.ts` 的 `libObjc` Proxy（懒加载 + 方法指针缓存）。

## 📂 文件清单

### 主模块

| 文档 | 源码 | 主要 RPC |
| --- | --- | --- |
| [binarycookies](/reference/agent/ios/binarycookies) | `ios/binarycookies.ts` | `iosCookiesGet` |
| [binary](/reference/agent/ios/binary) | `ios/binary.ts` | `iosBinaryInfo` |
| [bundles](/reference/agent/ios/bundles) | `ios/bundles.ts` | `iosBundles*` / `iosInfo` |
| [credentialstorage](/reference/agent/ios/credentialstorage) | `ios/credentialstorage.ts` | `iosUrlCredentialsDump` |
| [crypto](/reference/agent/ios/crypto) | `ios/crypto.ts` | `iosMonitorCrypto` |
| [filesystem](/reference/agent/ios/filesystem) | `ios/filesystem.ts` | `iosFile*` |
| [heap](/reference/agent/ios/heap) | `ios/heap.ts` | `iosHeap*` |
| [hooking](/reference/agent/ios/hooking) | `ios/hooking.ts` | `iosHooking*` |
| [jailbreak](/reference/agent/ios/jailbreak) | `ios/jailbreak.ts` | `iosJailbreak*` |
| [keychain](/reference/agent/ios/keychain) | `ios/keychain.ts` | `iosKeychain*` |
| [nsuserdefaults](/reference/agent/ios/nsuserdefaults) | `ios/nsuserdefaults.ts` | `iosNsuserDefaultsGet` |
| [pasteboard](/reference/agent/ios/pasteboard) | `ios/pasteboard.ts` | `iosPasteboardMonitor` |
| [pinning](/reference/agent/ios/pinning) | `ios/pinning.ts` | `iosPinningDisable` |
| [plist](/reference/agent/ios/plist) | `ios/plist.ts` | `iosPlistRead` |
| [userinterface](/reference/agent/ios/userinterface) | `ios/userinterface.ts` | `iosUi*` |

### lib 工具模块

| 文档 | 源码 | 作用 |
| --- | --- | --- |
| [lib/constants](/reference/agent/ios/lib/constants) | `ios/lib/constants.ts` | iOS 系统常量 |
| [lib/helpers](/reference/agent/ios/lib/helpers) | `ios/lib/helpers.ts` | 通用辅助（含 `arrayBufferToHex`） |
| [lib/interfaces](/reference/agent/ios/lib/interfaces) | `ios/lib/interfaces.ts` | 接口定义 |
| [lib/libobjc](/reference/agent/ios/lib/libobjc) | `ios/lib/libobjc.ts` | ObjC 桥 Proxy |
| [lib/types](/reference/agent/ios/lib/types) | `ios/lib/types.ts` | 类型别名 |

## 🔗 相关文档

- [Agent 总览](/reference/agent/)
- [rpc/ios 聚合](/reference/agent/rpc/ios)
- [Frida 与 Agent](/guide/frida-agent)
