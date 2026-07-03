# 🧪 测试模块文档

`tests/` 下每个测试文件验证 objection 一个源码模块的行为。本分区按测试目录结构逐文件讲解。

## 📂 文件清单

### API

| 文档 | 被测对象 |
| --- | --- |
| [api/agent-endpoints](/reference/tests/api/agent-endpoints) | `api/agent_endpoints.py` |

### commands/android

| 文档 | 被测对象 |
| --- | --- |
| [commands/android/clipboard](/reference/tests/commands/android/clipboard) | `commands/android/clipboard.py` |
| [commands/android/command](/reference/tests/commands/android/command) | `commands/android/command.py` |
| [commands/android/heap](/reference/tests/commands/android/heap) | `commands/android/heap.py` |
| [commands/android/hooking](/reference/tests/commands/android/hooking) | `commands/android/hooking.py` |
| [commands/android/intents](/reference/tests/commands/android/intents) | `commands/android/intents.py` |
| [commands/android/keystore](/reference/tests/commands/android/keystore) | `commands/android/keystore.py` |
| [commands/android/pinning](/reference/tests/commands/android/pinning) | `commands/android/pinning.py` |
| [commands/android/root](/reference/tests/commands/android/root) | `commands/android/root.py` |

### commands/ios

| 文档 | 被测对象 |
| --- | --- |
| [commands/ios/bundles](/reference/tests/commands/ios/bundles) | `commands/ios/bundles.py` |
| [commands/ios/cookies](/reference/tests/commands/ios/cookies) | `commands/ios/cookies.py` |
| [commands/ios/hooking](/reference/tests/commands/ios/hooking) | `commands/ios/hooking.py` |
| [commands/ios/jailbreak](/reference/tests/commands/ios/jailbreak) | `commands/ios/jailbreak.py` |
| [commands/ios/keychain](/reference/tests/commands/ios/keychain) | `commands/ios/keychain.py` |
| [commands/ios/nsurlcredentialstorage](/reference/tests/commands/ios/nsurlcredentialstorage) | `commands/ios/nsurlcredentialstorage.py` |
| [commands/ios/nsuserdefaults](/reference/tests/commands/ios/nsuserdefaults) | `commands/ios/nsuserdefaults.py` |
| [commands/ios/pasteboard](/reference/tests/commands/ios/pasteboard) | `commands/ios/pasteboard.py` |
| [commands/ios/pinning](/reference/tests/commands/ios/pinning) | `commands/ios/pinning.py` |
| [commands/ios/plist](/reference/tests/commands/ios/plist) | `commands/ios/plist.py` |

### commands（通用）

| 文档 | 被测对象 |
| --- | --- |
| [commands/agent-converted-json](/reference/tests/commands/agent-converted-json) | Agent JSON 转换 |
| [commands/command-history](/reference/tests/commands/command-history) | `commands/command_history.py` |
| [commands/device](/reference/tests/commands/device) | `commands/device.py` |
| [commands/filemanager](/reference/tests/commands/filemanager) | `commands/filemanager.py` |
| [commands/frida-commands](/reference/tests/commands/frida-commands) | `commands/frida_commands.py` |
| [commands/jobs](/reference/tests/commands/jobs) | `commands/jobs.py` |
| [commands/memory](/reference/tests/commands/memory) | `commands/memory.py` |
| [commands/mobile-packages](/reference/tests/commands/mobile-packages) | `commands/mobile_packages.py` |
| [commands/plugin-manager](/reference/tests/commands/plugin-manager) | `commands/plugin_manager.py` |
| [commands/ui](/reference/tests/commands/ui) | `commands/ui.py` |

### console

| 文档 | 被测对象 |
| --- | --- |
| [console/agent-cli](/reference/tests/console/agent-cli) | `console/agent_cli.py` |
| [console/cli](/reference/tests/console/cli) | `console/cli.py` |
| [console/completer](/reference/tests/console/completer) | `console/completer.py` |
| [console/repl](/reference/tests/console/repl) | `console/repl.py` |

### state

| 文档 | 被测对象 |
| --- | --- |
| [state/app](/reference/tests/state/app) | `state/app.py` |
| [state/jobs](/reference/tests/state/jobs) | `state/jobs.py` |

### utils

| 文档 | 被测对象 |
| --- | --- |
| [utils/patchers/android](/reference/tests/utils/patchers/android) | `utils/patchers/android.py` |
| [utils/patchers/base](/reference/tests/utils/patchers/base) | `utils/patchers/base.py` |
| [utils/patchers/github](/reference/tests/utils/patchers/github) | `utils/patchers/github.py` |
| [utils/patchers/ios](/reference/tests/utils/patchers/ios) | `utils/patchers/ios.py` |
| [utils/helpers](/reference/tests/utils/helpers) | `utils/helpers.py` |
| [utils/output](/reference/tests/utils/output) | `utils/output.py` |
| [helpers](/reference/tests/helpers) | `tests/helpers.py` 公共工具 |

## 🔗 相关文档

- [源码模块文档总览](/reference/)
