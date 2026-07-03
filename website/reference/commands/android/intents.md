# Android Intent 操作 <code>commands/android/intents.py</code>

该模块围绕 Android Intent 展开：分析隐式 Intent 流转、直接启动 Activity 或 Service。它属于 `android intent` 命令组，CLI 前缀为 `android intent <analyze_implicit_intents|launch_activity|launch_service>`，常用于探查导出组件、触发深层页面或服务。

## 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/commands/android/intents.py` |
| Agent 实现 | `agent/src/android/intent.ts` |
| 命令组 | `android intent` |
| 依赖 | `objection.state.connection`、`objection.utils.output`、`objection.utils.helpers`、`click` |

## 解决的问题

- 隐式 Intent 的目标组件难以静态追踪，需运行时记录调用链与目标。
- 导出 Activity/Service 可能是越权入口，直接拉起以验证可达性。
- 配合 `--dump-backtrace` 还原 Intent 发起上下文，定位漏洞触发点。

## 📋 命令清单

| 命令 | 函数 | 说明 |
| --- | --- | --- |
| `android intent analyze_implicit_intents [--dump-backtrace]` | `analyze_implicit_intents()` | hook 隐式 Intent，记录目标与栈 |
| `android intent launch_activity <class>` | `launch_activity()` | 通过 Intent 启动指定 Activity |
| `android intent launch_service <class>` | `launch_service()` | 通过 Intent 启动指定 Service |

辅助函数：`_should_dump_backtrace()`（行 10）。

## ⚙️ 实现原理

三个命令都很薄：取 API → 调 `api.android_intent_*` → JSON 模式返回 `CommandResult`。`analyze_implicit_intents` 注册异步作业，命中靠消息；`launch_activity`/`launch_service` 是同步触发。

### `analyze_implicit_intents()` — 分析隐式 Intent

源码：[`objection/commands/android/intents.py:21`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L21)

无位置参数，仅看 `--dump-backtrace` 标志。调 `api.android_intent_analyze(should_backtrace)` 注册 hook，拦截 `Context.startActivity`/`startService` 等。命中数据异步到达。

```python
# objection/commands/android/intents.py:25-28
api = state_connection.get_api()
should_backtrace = _should_dump_backtrace(args)
api.android_intent_analyze(should_backtrace)
```

### `launch_activity()` — 启动 Activity

源码：[`objection/commands/android/intents.py:46`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L46)

`args[0]` 为 Activity 全限定类名，调 `api.android_intent_start_activity(intent_class)`。agent 侧构造 `Intent` 并 `startActivity`。

```python
# objection/commands/android/intents.py:63-66
intent_class = args[0]
api = state_connection.get_api()
api.android_intent_start_activity(intent_class)
```

### `launch_service()` — 启动 Service

源码：[`objection/commands/android/intents.py:76`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L76)

同上，调 `api.android_intent_start_service(intent_class)`。

```mermaid
flowchart LR
    A["CLI 参数"] --> B["get_api"]
    B --> C["api.android_intent_* RPC"]
    C --> D["agent hook / 构造 Intent"]
    D --> E["analyze 异步消息 / launch 同步触发"]
    E --> F["click.secho 提示 / JSON CommandResult"]
```

## JSON 模式行为

- `analyze_implicit_intents`：返回 `result={'action', 'dump_backtrace'}`，`warnings` 提示作业 id 需经 `agent state` 查、Intent 活动走异步消息或 HTTP `/events`。
- `launch_activity`/`launch_service`：缺参数返回 `status='error'`；成功返回 `result={'action', 'activity'/'service'}`。
- 三者在非 JSON 模式均用 `click.secho` 给出粗体确认文本。

## 🔍 源码索引

| 符号 | 位置 |
| --- | --- |
| `_should_dump_backtrace` | [`objection/commands/android/intents.py:10`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L10) |
| `analyze_implicit_intents` | [`objection/commands/android/intents.py:21`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L21) |
| `launch_activity` | [`objection/commands/android/intents.py:46`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L46) |
| `launch_service` | [`objection/commands/android/intents.py:76`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/commands/android/intents.py#L76) |

## 相关文档

- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
