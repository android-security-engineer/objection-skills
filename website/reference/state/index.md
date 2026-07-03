# 🔌 状态层文档

`objection/state/` 管理 objection 与 Frida 的连接、设备、应用、文件管理器与作业的全局状态，并把 agent 的 RPC 方法包装成 Python 可调接口。本分区逐文件讲解。

## 📂 文件清单

| 文档 | 源码 | 职责 |
| --- | --- | --- |
| [connection](/reference/state/connection) | `state/connection.py` | Frida session/agent attach，`get_api()` 单例 |
| [app](/reference/state/app) | `state/app.py` | 应用句柄状态 |
| [device](/reference/state/device) | `state/device.py` | 设备与平台信息 |
| [filemanager](/reference/state/filemanager) | `state/filemanager.py` | 远程文件管理器句柄与 cwd |
| [jobs](/reference/state/jobs) | `state/jobs.py` | 作业注册表 |
| [api](/reference/state/api) | `state/api.py` | RPC 方法包装层 |

## 🔗 相关文档

- [整体架构](/guide/architecture)
- [RPC 通信机制](/guide/rpc)
