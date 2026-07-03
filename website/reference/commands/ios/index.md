# 🍎 iOS 命令模块文档

`objection/commands/ios/` 下的每个 Python 文件实现一组 `ios ...` REPL 命令。本分区逐文件讲解。

> 这些命令在目标 iOS 进程内的实现，见 [agent TS · ios](/reference/agent/)。

## 📂 文件清单

| 文档 | 源码 | 命令组 |
| --- | --- | --- |
| [binary](/reference/commands/ios/binary) | `commands/ios/binary.py` | `ios info binary` |
| [bundles](/reference/commands/ios/bundles) | `commands/ios/bundles.py` | `ios info` / `ios bundles` |
| [cookies](/reference/commands/ios/cookies) | `commands/ios/cookies.py` | `ios cookies` |
| [generate](/reference/commands/ios/generate) | `commands/ios/generate.py` | `ios hooking generate` |
| [heap](/reference/commands/ios/heap) | `commands/ios/heap.py` | `ios heap` |
| [hooking](/reference/commands/ios/hooking) | `commands/ios/hooking.py` | `ios hooking` |
| [jailbreak](/reference/commands/ios/jailbreak) | `commands/ios/jailbreak.py` | `ios jailbreak` |
| [keychain](/reference/commands/ios/keychain) | `commands/ios/keychain.py` | `ios keychain` |
| [monitor](/reference/commands/ios/monitor) | `commands/ios/monitor.py` | `ios monitor crypto` |
| [nsurlcredentialstorage](/reference/commands/ios/nsurlcredentialstorage) | `commands/ios/nsurlcredentialstorage.py` | `ios nsurlcredentialstorage` |
| [nsuserdefaults](/reference/commands/ios/nsuserdefaults) | `commands/ios/nsuserdefaults.py` | `ios nsuserdefaults` |
| [pasteboard](/reference/commands/ios/pasteboard) | `commands/ios/pasteboard.py` | `ios pasteboard` |
| [pinning](/reference/commands/ios/pinning) | `commands/ios/pinning.py` | `ios sslpinning` |
| [plist](/reference/commands/ios/plist) | `commands/ios/plist.py` | `ios plist` |

## 🔗 相关文档

- [命令速查总览](/reference/cli/)
- [iOS 功能详解](/features/ios-keychain)
