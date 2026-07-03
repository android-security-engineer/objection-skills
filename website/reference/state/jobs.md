# 任务注册表 <code>objection/state/jobs.py</code>

objection 的「后台任务注册表」单例。一个 Job 代表一组持续生效的 hook 或一段独立注入的 Frida 脚本（如 `android hooking watch`、`android sslpinning disable`）。`JobManagerState` 维护 `uuid → Job` 字典，负责注册、移除与进程退出时的统一清理，并通过 `atexit` 保证 hook 被还原。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/state/jobs.py` |
| 类型 | 状态（State，进程级单例） |
| 被谁调用 | `commands/jobs.py`（list/kill）、`commands/android/hooking.py`、`commands/android/pinning.py` 等创建持久 hook 的命令、`utils/agent.py`（脚本型 Job 与 teardown） |
| 依赖 | `click`、`frida`、`objection.state.connection.state_connection` |

## 🎯 解决的问题
- 给每个长生命周期 hook 一个稳定标识（uuid），让 `jobs list` / `jobs kill <id>` 可定位。
- 区分两种 Job 生命周期：`script` 型（本地 `frida.Script`，靠 `unload()` 终止）与 `hook` 型（agent 侧注册的 hook，靠 RPC `jobs_kill` 终止）。
- 进程退出时统一卸载所有脚本并通知 agent 清理 hook，避免设备侧残留。

## 🏗️ 核心结构

### `Job` — 单个任务
源码：`objection/state/jobs.py:10`

```python
def __init__(self, name, job_type, handle, uuid: int = None) -> None:
    if uuid is not None:
        try:
            self.uuid = int(uuid)
        except (ValueError, TypeError):
            # identifier 可能是 base36 字符串（如 rdcjq16g8xi），原样保留
            self.uuid = uuid
    else:
        self.uuid = randint(100000, 999999)
    self.name = name
    self.job_type = job_type
    self.handle = handle
```

字段：
- `uuid`：任务标识。调用方可传入（agent 侧 hook 返回的 base36 字符串如 `rdcjq16g8xi`），无法 `int()` 时原样保留；未传入则随机生成 6 位整数。
- `name`：人类可读名（如 `Watch com.foo.Bar.login`）。
- `job_type`：`'script'` 或 `'hook'`，决定 `end()` 的清理路径。
- `handle`：`script` 型为 `frida.Script`，`hook` 型无实际句柄（清理走 RPC）。

### `Job.end` — 按类型清理
源码：`objection/state/jobs.py:35`

```python
def end(self):
    if self.job_type == "script":
        click.secho("[job manager] Killing job {0}...".format(self.uuid), dim=True)
        self.handle.unload()
    elif self.job_type == "hook":
        api = state_connection.get_api()
        api.jobs_kill(self.uuid)
    else:
        click.secho(('[job {0}] - Unknown job type {1}'.format(self.uuid, self.job_type)), fg='red', dim=True)
```

两条清理路径：
- `script`：直接调 `frida.Script.unload()`，本地卸载。
- `hook`：经 `state_connection.get_api()` 拿到 RPC，调 agent 侧的 `jobs_kill(uuid)` 让 agent 自己摘除 hook。

```mermaid
flowchart LR
    HCMD["hooking/pinning 命令"] -->|创建 Job(job_type=hook)| JM["JobManagerState"]
    SCMD["agent.attach_script / 插件"] -->|创建 Job(job_type=script)| JM
    JM -->|jobs list| USER["REPL 用户"]
    USER -->|jobs kill id| JM
    JM -->|job.end| HOOKEND["hook: api.jobs_kill(uuid)"]
    JM -->|job.end| SCRIPTEND["script: handle.unload()"]
    ATEXIT["atexit"] -->|cleanup| JM
```

### `JobManagerState` — 注册表
源码：`objection/state/jobs.py:53`

```python
def __init__(self) -> None:
    self.jobs: dict[int, Job] = {}
    atexit.register(self.cleanup)
```

构造时注册 `atexit` 钩子，确保解释器退出时统一清理。

#### `add_job` — 去重注册
源码：`objection/state/jobs.py:67`

```python
def add_job(self, new_job: Job) -> None:
    if new_job.uuid not in self.jobs:
        self.jobs[new_job.uuid] = new_job
```

#### `remove_job` — 弹出并终止
源码：`objection/state/jobs.py:79`

```python
def remove_job(self, job_uuid: int):
    if job_uuid not in self.jobs:
        click.secho(f"Error: Job with ID {job_uuid} does not exist.", fg='red')
        return
    job_to_remove = self.jobs.pop(job_uuid)
    job_to_remove.end()
```

不存在时打印红色错误并返回，不抛异常。

#### `cleanup` — 批量卸载
源码：`objection/state/jobs.py:93`

```python
def cleanup(self) -> None:
    for uuid in list(self.jobs.keys()):
        try:
            job = self.jobs.pop(uuid)
            job.end()
        except frida.InvalidOperationError:
            click.secho(('[job manager] Job: {0} - An error occurred stopping job. '
                         'Device may no longer be available.'.format(uuid)), fg='red', dim=True)
```

逐个 `pop` + `end()`；若设备已掉线（`frida.InvalidOperationError`），打印警告但继续清理其余 Job。`list(self.jobs.keys())` 复制键视图，避免迭代中修改字典。

### 模块级单例
源码：`objection/state/jobs.py:113`

```python
job_manager_state = JobManagerState()
```

## ⚙️ 实现要点
- **uuid 的两种来源**：本地随机 6 位整数（默认）或 agent 侧返回的 base36 字符串（如 `rdcjq16g8xi`）。`int(uuid)` 失败时原样保留——这是为兼容 agent 侧 hook 标识格式而做的容错（见 `:26-28` 注释）。
- **`atexit` 兜底**：`JobManagerState` 在构造时注册 `atexit.register(self.cleanup)`，保证 `Agent.teardown()` 与解释器退出两条路径都会触发清理。`Agent.teardown()`（`utils/agent.py:397`）也显式调 `job_manager_state.cleanup()`。
- **`script` vs `hook` 双轨**：`script` 型 Job 由 `Agent.attach_script()`（`utils/agent.py:308`）创建，用于独立脚本注入；`hook` 型由 hooking/pinning 等命令创建，依赖 agent 侧 RPC 管理。`end()` 据类型分派，避免本地脚本与远程 hook 混用清理路径。
- **Agent 友好性**：`commands/jobs.py` 在 JSON 模式下把 `jobs` 字典序列化进 `CommandResult.result`，Agent 可直接拿到 `[{uuid, name, type}, ...]` 列表，无需解析终端文本。

## 🔍 源码索引
| 符号 | 位置 |
| --- | --- |
| `Job` | `objection/state/jobs.py:10` |
| `Job.__init__` | `objection/state/jobs.py:13` |
| `Job.end` | `objection/state/jobs.py:35` |
| `JobManagerState` | `objection/state/jobs.py:53` |
| `JobManagerState.__init__` | `objection/state/jobs.py:56` |
| `add_job` | `objection/state/jobs.py:67` |
| `remove_job` | `objection/state/jobs.py:79` |
| `cleanup` | `objection/state/jobs.py:93` |
| `job_manager_state`（单例） | `objection/state/jobs.py:113` |

## 🔗 相关文档
- [整体架构](/guide/architecture)
- [RPC 通信机制](/guide/rpc)
- [REPL 与命令](/guide/repl)
- [面向 AI Agent 使用](/guide/agent-usage)
