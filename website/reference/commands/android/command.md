# Android Shell 命令执行 <code>commands/android/command.py</code>

该模块在目标 Android 进程上下文中执行任意 shell 命令，把 stdout/stderr 回传给调用方。它属于 `android shell_exec` 命令，CLI 前缀即 `android shell_exec`，常用于在已注入的 App 沙箱里探查文件、跑 `ls`/`id`/`pm` 等。

## 模块概览

| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/commands/android/command.py` |
| Agent 实现 | `agent/src/android/shell.ts` |
| 命令组 | `android shell_exec` |
| 依赖 | `objection.state.connection`、`objection.utils.output`、`click` |

## 解决的问题

- App 沙箱内的 shell 执行权限与 App 相同，可验证降权/提权边界、读取 App 私有目录。
- 无需 adb：命令通过 Frida RPC 在目标进程内执行，绕过设备 USB 调试限制。
- 为自动化脚本提供结构化的 stdout/stderr JSON 输出。

## 📋 命令清单

| 命令 | 函数 | 说明 |
| --- | --- | --- |
| `android shell_exec <cmd...>` | `execute()` | 在目标进程执行 shell 命令并回传输出 |

## ⚙️ 实现原理

Python 把所有位置参数用空格拼成单条命令字符串，调用 `api.android_shell_exec(command)`，agent 侧通过 `Java.use('java.lang.Runtime').exec(...)` 之类机制执行并采集 `stdOut`/`stdErr`。返回值是 dict，Python 抽取两路输出分别渲染。

### `execute()` — 执行 shell 命令

源码：`objection/commands/android/command.py:9`

先把 `args` 拼成命令串；非 JSON 模式下用 `click.secho` 灰字回显命令本身。调 RPC 拿到 `response` dict 后，对 `stdOut` 用粗体、`stdErr` 用红色粗体分别打印。JSON 模式则把 `command`/`stdout`/`stderr` 打包进 `CommandResult`。

```python
# objection/commands/android/command.py:17-23
command = ' '.join(args)
json_mode = should_output_json(args)
if not json_mode:
    click.secho('Running shell command: {0}\n'.format(command), dim=True)

api = state_connection.get_api()
response = api.android_shell_exec(command)
```

```python
# objection/commands/android/command.py:25-39
stdout = response.get('stdOut', '') if isinstance(response, dict) else ''
stderr = response.get('stdErr', '') if isinstance(response, dict) else ''

if not json_mode:
    if 'stdOut' in response and len(response['stdOut']) > 0:
        click.secho(response['stdOut'], bold=True)
    if 'stdErr' in response and len(response['stdErr']) > 0:
        click.secho(response['stdErr'], bold=True, fg='red')

if json_mode:
    return output_result(
        CommandResult(result={'command': command, 'stdout': stdout, 'stderr': stderr}),
        command='android shell_exec',
    )
```

```mermaid
flowchart LR
    A["CLI 参数列表"] --> B["' '.join 拼命令串"]
    B --> C["get_api"]
    C --> D["api.android_shell_exec RPC"]
    D --> E["agent Runtime.exec 采集输出"]
    E --> F["stdout 粗体 / stderr 红字 / JSON"]
```

## JSON 模式行为

JSON 模式下跳过命令回显与彩色打印，直接返回 `CommandResult(result={'command', 'stdout', 'stderr'})`。对 `response` 做了 `isinstance(response, dict)` 防御，避免 agent 返回异常类型时崩溃——非 dict 时 stdout/stderr 退化为空串。

## 🔍 源码索引

| 符号 | 位置 |
| --- | --- |
| `execute` | `objection/commands/android/command.py:9` |

## 相关文档

- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
