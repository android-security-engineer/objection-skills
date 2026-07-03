# iOS 剪贴板监控 <code>commands/ios/pasteboard.py</code>

本模块用于启动一个长期 Job 监控 iOS `UIPasteboard`，当剪贴板出现新的字符串内容时实时上报。常用于捕获 App 复制的敏感文本（密码、2FA、Token）。命令组前缀为 `ios pasteboard ...`。

## 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/commands/ios/pasteboard.py` |
| Agent 实现 | `agent/src/ios/pasteboard.ts` |
| 命令组 | `ios pasteboard ...` |
| 依赖 | `objection.state.connection`、`objection.utils.output` |

## 解决的问题

- 想被动等待 App 把敏感字符串写入剪贴板，而非主动枚举。
- 监控是长期 Hook，新字符串由 Agent 异步消息发出，Agent 流程需明确轮询方式。
- 与 Android clipboard 模块对应，iOS 侧仅提供「监控」动作。

## 命令清单

| 命令 | 函数 | 说明 |
| --- | --- | --- |
| `ios pasteboard monitor` | `monitor()` | 启动剪贴板字符串监控 Job |

## 实现原理

Python 层极简：调用 `ios_monitor_pasteboard()` 安装监控 Hook，无参数、无返回数据处理。新字符串由 Agent 以异步消息发出，因此 JSON 模式带两条 warning。

### `monitor()` — 启动监控

源码：[`objection/commands/ios/pasteboard.py:7`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/ios/pasteboard.py#L7)

```python
# objection/commands/ios/pasteboard.py:16-17
api = state_connection.get_api()
api.ios_monitor_pasteboard()
```

JSON 模式返回见 [`objection/commands/ios/pasteboard.py:19-27`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/ios/pasteboard.py#L19)：

```python
CommandResult(
    result={'action': 'monitoring_pasteboard'},
    warnings=['Job id not surfaced; use `agent state` to list running jobs.',
              'New pasteboard strings arrive as async messages.'],
)
```

```mermaid
flowchart LR
    A["monitor(args)"] --> B["ios_monitor_pasteboard()"]
    B --> C["安装 UIPasteboard 监控"]
    C --> D["新字符串 → 异步消息"]
    D --> E["轮询: agent state / /events"]
```

## JSON 模式行为

返回 `CommandResult(result={'action': 'monitoring_pasteboard'})`，命令名 `ios pasteboard monitor`。两条 warning 提示 Job id 未暴露、新字符串以异步消息到达，需轮询 `agent state` 或 HTTP `/events`。非 JSON 模式静默返回 `None`。

## 源码索引

| 符号 | 位置 |
| --- | --- |
| `monitor` | [`objection/commands/ios/pasteboard.py:7`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/ios/pasteboard.py#L7) |

## 相关文档

- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
