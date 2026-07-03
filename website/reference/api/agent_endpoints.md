# 面向 Agent 的 HTTP 端点 <code>objection/api/agent_endpoints.py</code>

为 AI Agent 设计的命令层 HTTP 端点。与 `rpc.py`（直接桥接 Frida RPC exports）不同，这组端点工作在 **objection 命令层**——接收 objection 命令字符串、复用统一输出层（`objection/utils/output`）、返回固定 JSON schema。Agent 可通过这组端点执行命令、查状态、轮询事件、自发现能力、直调 RPC。

## 📋 模块概览
| 项目 | 值 |
| --- | --- |
| 文件路径 | `objection/api/agent_endpoints.py` |
| 类型 | API 端点（Flask Blueprint，新增模块） |
| 被谁调用 | `objection/api/app.py` 的 `create_app()` 注册（空前缀，端点挂在根路径） |
| 依赖 | `flask.Blueprint`/`jsonify`/`request`/`abort`、`objection.state.connection.state_connection`、`objection.state.jobs.job_manager_state`、`objection.utils.events.drain_events`/`peek_events`、`objection.utils.helpers.to_snake_case`、`objection.utils.output`（`CommandResult`/`output_result`/`push_result_capture`/`pop_result_capture`/`set_json_output`/`is_json_output`）、`objection.console.repl.Repl`、`objection.console.commands.COMMANDS`、`objection.console.agent_cli._enumerate_capabilities` |

## 🎯 解决的问题
- **Agent 需要命令层而非 RPC 层**：`/rpc/invoke` 暴露的是 Frida agent 的底层 exports（`android_hooking_list_classes` 等），Agent 要自己拼参数、解析原始返回。本端点接收 objection 命令字符串（`android hooking list classes`），复用人类命令的全部逻辑（参数解析、输出格式化、Job 管理），让 Agent 用「说命令」的方式驱动 objection。
- **统一 JSON schema**：所有端点返回 `{status, command, result, jobs_created, warnings}` 五字段结构，Agent 解析逻辑只写一次。错误也走同一 schema（带 `status: 'error'` + HTTP 4xx/5xx）。
- **异步事件可轮询**：Hook 命中、canary 触发等异步结果不能通过命令调用同步拿到。`/events/poll` 让 Agent 在执行 hook 命令后周期性拉取事件缓冲。
- **能力自发现**：Agent 不可能预先知道所有 objection 命令。`/capabilities` 返回命令注册表快照（不需要设备连接），Agent 可据此构造合法命令。
- **状态感知**：多步流程中 Agent 需知「现在连了什么设备、有哪些 Job 在跑」。`/state` 返回连接信息 + Job 列表。
- **强制 JSON 模式**：人类模式输出是人类可读文本，Agent 需要结构化。所有端点先 `_ensure_json_mode()` 把全局输出切到 JSON。

## 🏗️ 核心结构

### `bp` — Agent API 蓝图
源码：[`objection/api/agent_endpoints.py:34`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L34)

```python
bp = Blueprint('agent_api', __name__, url_prefix='')
```

空前缀，端点挂在根路径：`POST /command/exec`、`GET /state`、`GET /events/poll`、`GET /capabilities`、`GET/POST /agent/rpc/<method>`。

### `_ensure_json_mode` — 强制 JSON 输出
源码：[`objection/api/agent_endpoints.py:37`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L37)

```python
def _ensure_json_mode():
    if not is_json_output():
        set_json_output(True)
```

每个端点入口先调它。`set_json_output(True)` 是全局开关，让 `utils/output` 与 `utils/events` 的 `record_event` 走 JSON 分支（缓冲事件、产出 `CommandResult` 结构）。

### `_no_agent_response` — 无 agent 统一错误
源码：[`objection/api/agent_endpoints.py:44`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L44)

```python
def _no_agent_response():
    return jsonify({
        'status': 'error',
        'command': '',
        'result': {'error': 'no agent is connected; start objection with `objection api` first'},
        'jobs_created': [],
        'warnings': [],
    }), 503
```

未注入 agent 时返回 503 + 统一 schema。提示用户用 `objection api` 启动（HTTP 服务器与 agent 共进程）。

### `command_exec` — 执行 objection 命令
源码：[`objection/api/agent_endpoints.py:56`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L56)

```python
@bp.route('/command/exec', methods=('POST',))
def command_exec():
    _ensure_json_mode()

    if not state_connection.agent:
        return _no_agent_response()

    post_data = request.get_json(force=True, silent=True)
    if not post_data:
        return abort(jsonify(message='POST request without a valid JSON body received'))

    commands = []
    if 'command' in post_data:
        commands = [post_data['command']]
    elif 'commands' in post_data:
        commands = list(post_data['commands'])
    else:
        return abort(jsonify(message='JSON body must contain "command" or "commands"'))

    from objection.console.repl import Repl
    repl = Repl()

    results = []
    for cmd in commands:
        buf = push_result_capture()
        try:
            repl.run_command(cmd)
        except Exception as e:
            output_result(
                CommandResult(result={'error': str(e)}, status='error',
                              human_text='Command failed: {0}'.format(e), exit_code=1),
                command=cmd,
            )
        captured = pop_result_capture() or []

        if not captured:
            results.append({
                'status': 'ok',
                'command': cmd,
                'result': None,
                'jobs_created': [],
                'warnings': ['command produced no structured output; it may be unconverted or interactive-only.'],
            })
        else:
            last = captured[-1]
            if len(captured) > 1:
                last = dict(last)
                last.setdefault('warnings', [])
                last['warnings'] = list(last['warnings']) + [
                    'command emitted {0} structured payloads; only the last is returned as result.'.format(len(captured))
                ]
            results.append(last)

    if len(results) == 1:
        return jsonify(results[0])
    return jsonify(results)
```

核心机制：**结果捕获（result capture）**。objection 命令的人类模式直接打印 stdout，Agent 模式需要结构化结果。`push_result_capture()` 在输出层挂一个捕获缓冲，`repl.run_command(cmd)` 执行命令时，已改造的命令会调 `output_result(CommandResult(...))` 把结构化结果推入缓冲；`pop_result_capture()` 取出缓冲。

- 单命令（`{"command": "..."}`）→ 返回单对象；多命令（`{"commands": [...]}`）→ 返回数组。
- 命令抛异常 → 构造 `CommandResult(status='error')` 入队，仍返回结构化结果而非 500。
- 命令无结构化输出（未改造或交互式）→ 返回 `result: None` + warning 提示 Agent。
- 多条结构化输出 → 取最后一条作 result，其余在 warning 里告知。

延迟导入 `Repl` 避免循环依赖（repl 依赖 cli，cli 依赖 agent_cli）。

### `state` — 会话状态快照
源码：[`objection/api/agent_endpoints.py:133`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L133)

```python
@bp.route('/state', methods=('GET',))
def state():
    _ensure_json_mode()
    if not state_connection.agent:
        return _no_agent_response()

    sc = state_connection
    agent_obj = sc.get_agent() if sc.agent else None

    jobs = []
    try:
        from objection.commands.jobs import sync_job_manager
        sync_job_manager()
        for uuid, job in job_manager_state.jobs.items():
            jobs.append({'id': uuid, 'type': job.job_type, 'name': job.name})
    except Exception:
        pass

    state_data = {
        'connection': {
            'type': sc.device_type, 'network': sc.network, 'host': sc.host, 'port': sc.port,
            'device_id': sc.device_id, 'name': sc.name, 'spawn': sc.spawn, 'foremost': sc.foremost,
        },
        'pid': getattr(agent_obj, 'pid', None) if agent_obj else None,
        'jobs': jobs,
    }
    return jsonify({'status': 'ok', 'command': '/state', 'result': state_data, 'jobs_created': [], 'warnings': []})
```

返回连接元信息（设备类型、host/port、device_id 等）+ agent pid + 运行中的 Job 列表。`sync_job_manager()` 先与设备同步 Job 状态（Frida 端 Job 可能已退出）再枚举。Job 块用 try/except 兜住——Job 同步失败不应让整个 state 请求失败。

### `events_poll` — 事件轮询
源码：[`objection/api/agent_endpoints.py:185`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L185)

```python
@bp.route('/events/poll', methods=('GET',))
def events_poll():
    _ensure_json_mode()

    if 'peek' in request.args:
        from objection.utils.events import peek_events
        data = peek_events()
    else:
        data = drain_events()

    return jsonify({
        'status': 'ok', 'command': '/events/poll', 'result': data, 'jobs_created': [], 'warnings': [],
    })
```

默认 `drain_events()`（取出并清空队列），`?peek=1` 走 `peek_events()`（只看不清空）。结果包进统一 schema 的 `result` 字段。事件队列由 `utils/events.py` 维护，Frida `script.on('message')` 回调入队（仅在 JSON 模式）。

### `capabilities` — 命令自发现
源码：[`objection/api/agent_endpoints.py:213`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L213)

```python
@bp.route('/capabilities', methods=('GET',))
def capabilities():
    _ensure_json_mode()

    from objection.console.commands import COMMANDS
    from objection.console.agent_cli import _enumerate_capabilities

    caps = _enumerate_capabilities(COMMANDS)
    return jsonify({
        'status': 'ok', 'command': '/capabilities',
        'result': {'commands': caps}, 'jobs_created': [], 'warnings': [],
    })
```

不需要设备连接——纯静态注册表快照。`_enumerate_capabilities`（来自 `agent_cli`）遍历 `COMMANDS` 注册表，产出每个命令的结构化描述（名称、参数、用途），供 Agent 自主构造合法命令。

### `agent_rpc` — 直调 agent RPC
源码：[`objection/api/agent_endpoints.py:236`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L236)

```python
@bp.route('/agent/rpc/<string:method>', methods=('GET', 'POST'))
def agent_rpc(method):
    _ensure_json_mode()
    if not state_connection.agent:
        return _no_agent_response()

    method_name = to_snake_case(method)
    args_list = []
    if request.method == 'POST':
        post_data = request.get_json(force=True, silent=True)
        if post_data is None:
            return abort(jsonify(message='POST request without a valid JSON body received'))
        if not isinstance(post_data, list):
            return abort(jsonify(message='POST body must be a JSON array of positional arguments'))
        args_list = post_data

    try:
        api = state_connection.get_api()
        fn = getattr(api, method_name, None)
        if fn is None:
            raise AttributeError('unknown RPC method: {0}'.format(method_name))
        result = fn(*args_list)
    except Exception as e:
        return jsonify({
            'status': 'error', 'command': '/agent/rpc/{0}'.format(method),
            'result': {'error': str(e)}, 'jobs_created': [], 'warnings': [],
        }), 500

    return jsonify({
        'status': 'ok', 'command': '/agent/rpc/{0}'.format(method),
        'result': result, 'jobs_created': [], 'warnings': [],
    })
```

与 `/rpc/invoke` 功能类似但区别明显：

| 维度 | `/rpc/invoke` (rpc.py) | `/agent/rpc/<method>` (本端点) |
| --- | --- | --- |
| POST body | JSON 对象（`.values()` 作参数） | JSON 数组（位置参数） |
| 响应格式 | `jsonify(response)` 原始 | 统一 schema `{status, result, ...}` |
| 错误格式 | 400 + `{message}` | 500 + 统一 schema `status:'error'` |
| 未知方法 | `getattr` 抛异常 → 400 | 显式 `AttributeError` → 500 + 统一 schema |

本端点是「Agent 友好版 RPC」——强制 JSON 数组参数、统一 schema、明确的方法不存在错误。

```mermaid
flowchart TD
    AGENT["AI Agent"] -->|"POST /command/exec<br/>{command: 'android hooking watch class ...'}"| CMD
    AGENT -->|"GET /state"| ST
    AGENT -->|"GET /events/poll"| EV
    AGENT -->|"GET /capabilities"| CAP
    AGENT -->|"POST /agent/rpc/m<br/>[arg1, arg2]"| RPC

    CMD["command_exec"] --> JM["_ensure_json_mode"]
    JM --> REPL["Repl.run_command(cmd)"]
    REPL --> CAPTURE["push/pop_result_capture<br/>结构化结果缓冲"]
    CAPTURE --> RES1["统一 schema (单/多数组)"]

    ST["state"] --> SYNC["sync_job_manager"]
    SYNC --> RES2["connection + pid + jobs"]

    EV["events_poll"] --> DRAIN{"?peek=1?"}
    DRAIN -->|是| PEEK["peek_events"]
    DRAIN -->|否| DRAIN2["drain_events"]
    PEEK --> RES3["{events, dropped, remaining}"]
    DRAIN2 --> RES3

    CAP["capabilities"] --> ENUM["_enumerate_capabilities(COMMANDS)"]
    ENUM --> RES4["静态命令注册表"]

    RPC["agent_rpc"] --> SNAKE["to_snake_case"]
    SNAKE --> GETATTR["getattr(api, method)"]
    GETATTR --> RES5["统一 schema 或 500"]

    subgraph 异步事件来源
        FRIDA["Frida script.on('message')"] --> REC["record_event (JSON 模式)"]
        REC --> QUEUE["_events deque"]
    end
    QUEUE -.-> DRAIN
```

## ⚙️ 实现要点
- **结果捕获机制是核心创新**：objection 命令的人类模式调 `click.echo` / `print`，改造为 Agent 模式不是重写每个命令，而是加一层 `output_result(CommandResult(...))`。`push_result_capture`/`pop_result_capture`（来自 `utils/output`）在输出层挂一个线程局部缓冲，让命令实现里的 `output_result` 调用被捕获而非直接打印。这样未改造的命令（不调 `output_result`）会落到「no structured output」分支，已改造的命令自动产出结构化结果——渐进迁移。
- **多命令批处理**：`{"commands": [...]}` 一次调多个命令，返回数组。比 Agent 逐条 HTTP 调用省往返；但命令间无依赖传递（每条独立捕获），适合批量查询而非流水线。
- **`sync_job_manager` 用 try/except 兜底**：`/state` 端点里 Job 同步失败被吞，`jobs` 返回空列表而非让整个请求 500。设计哲学：状态查询应尽可能成功，部分失败降级而非全失败。
- **`/capabilities` 不需要设备**：纯静态注册表，Agent 可在连接设备前先调它了解能力。这让 Agent 能做「先看能力 → 选命令 → 连设备 → 执行」的规划流程。
- **`/agent/rpc` 强制 JSON 数组**：与 `/rpc/invoke` 的 JSON 对象不同，数组语义更清晰（位置参数就是有序的）。`isinstance(post_data, list)` 校验，非数组直接 400——避免 Agent 误传对象导致参数乱序。
- **统一 schema 的 `command` 字段**：每条响应都带 `command`（执行的命令字符串或端点路径），方便 Agent 在日志/对话里对齐请求与响应。`/agent/rpc/foo` 的 `command` 字段是 `/agent/rpc/foo`（保留原 method 名，未转 snake_case），便于 Agent 回溯。
- **延迟导入避免循环依赖**：`command_exec` 内 `from objection.console.repl import Repl`、`state` 内 `from objection.commands.jobs import sync_job_manager`、`capabilities` 内 `from objection.console.commands import COMMANDS` 与 `from objection.console.agent_cli import _enumerate_capabilities`——都在函数体内导入，避免模块加载时 `api.agent_endpoints` → `console.repl` → `console.cli` → `console.agent_cli` 的循环。
- **`_ensure_json_mode` 每端点都调**：因为 HTTP 服务器可能被人类命令复用（同一进程既跑人类 repl 又跑 HTTP API），全局 JSON 开关可能被人类模式重置。每端点入口强制重设，保证 Agent 请求一定走 JSON 分支。

## 🔍 源码索引
| 符号 | 位置 |
| --- | --- |
| `bp` | [`objection/api/agent_endpoints.py:34`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L34) |
| `_ensure_json_mode` | [`objection/api/agent_endpoints.py:37`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L37) |
| `_no_agent_response` | [`objection/api/agent_endpoints.py:44`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L44) |
| `command_exec` | [`objection/api/agent_endpoints.py:56`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L56) |
| `state` | [`objection/api/agent_endpoints.py:133`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L133) |
| `events_poll` | [`objection/api/agent_endpoints.py:185`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L185) |
| `capabilities` | [`objection/api/agent_endpoints.py:213`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L213) |
| `agent_rpc` | [`objection/api/agent_endpoints.py:236`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L236) |

## 🗺️ 端点路由全景图

下图刻画 `agent_endpoints.bp`（空前缀）注册的 5 个端点的路由、HTTP 方法、设备依赖性，以及它们与 `rpc.bp`（`/rpc` 前缀）、`script.bp`（`/script` 前缀）的位置关系。

```mermaid
flowchart TD
    subgraph agent_endpoints.bp url_prefix=''
        CE["POST /command/exec<br/>需 agent"]
        ST["GET /state<br/>需 agent"]
        EV["GET /events/poll<br/>不需 agent (读本地缓冲)"]
        CAP["GET /capabilities<br/>不需 agent (静态注册表)"]
        ARPC["GET/POST /agent/rpc/<method><br/>需 agent"]
    end

    subgraph rpc.bp url_prefix='/rpc'
        RINV["GET/POST /rpc/invoke/<method><br/>需 agent"]
    end

    subgraph script.bp url_prefix='/script'
        SR["POST /script/runonce<br/>需 agent"]
    end

    CE -->|复用| REPL["Repl.run_command"]
    ARPC -->|互补| RINV
    RINV -->|原始 RPC| AGJS["agent.js exports"]
    ARPC -->|统一 schema| AGJS

    CAP -->|静态| CMDREG["COMMANDS 注册表"]
    ST -->|同步| JM["job_manager_state + sync_job_manager"]
    EV -->|读| DEQUE["utils/events._events deque"]
```

路由设计要点（基于 [`agent_endpoints.py:34`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L34)）：

- **空前缀抢占根路径**：`agent_endpoints.bp` 用 `url_prefix=''`，端点直接挂在 `/command/exec`、`/state` 等根路径。这是刻意设计——Agent 端点是 objection HTTP API 的"主入口"，短 URL 便于 Agent 构造请求。代价是占用了根命名空间，插件蓝图若也用空前缀且注册同名路由会冲突。
- **设备依赖性分级**：`/command/exec`、`/state`、`/agent/rpc/<method>` 需要已注入 agent（未注入返回 503，[`agent_endpoints.py:44-53`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L44)）；`/capabilities` 是纯静态注册表快照，不需要设备（[`agent_endpoints.py:213`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L213)）；`/events/poll` 读本地事件缓冲，技术上不需要 agent 在线（但缓冲里的事件是 agent 产生的，agent 离线后缓冲仍可读）。
- **`/agent/rpc` 与 `/rpc/invoke` 路由共存**：两者都按 `<method>` 路由参数匹配，但前缀不同（`/agent/rpc/` vs `/rpc/invoke/`），Flask 路由层能区分。前者是"Agent 友好版"（统一 schema、JSON 数组参数），后者是"裸桥接版"（原始响应、JSON 对象参数）。

## 🔁 command_exec 结果捕获时序

下图刻画 `/command/exec` 的核心机制——结果捕获（result capture）的完整时序，展示 `push_result_capture`/`pop_result_capture` 如何拦截命令的结构化输出。

```mermaid
sequenceDiagram
    participant C as Agent 客户端
    participant CE as command_exec()
    participant OUT as utils/output
    participant R as Repl.run_command
    participant CMD as 命令实现
    participant JS as agent.js

    C->>CE: POST /command/exec {"command":"android hooking list classes"}
    CE->>CE: _ensure_json_mode()
    CE->>CE: state_connection.agent 检查
    CE->>OUT: push_result_capture()
    Note over OUT: 挂载线程局部捕获缓冲
    CE->>R: run_command("android hooking list classes")
    R->>R: 解析 token, 找 exec 方法
    R->>CMD: android_hooking.show_android_classes([])
    CMD->>JS: RPC 调用
    JS-->>CMD: 类列表数据
    CMD->>OUT: output_result(CommandResult(result=..., status='ok'))
    Note over OUT: 结果入捕获缓冲 (而非打印 stdout)
    CMD-->>R: 完成
    R-->>CE: 返回
    CE->>OUT: pop_result_capture()
    OUT-->>CE: captured = [CommandResult...]
    alt captured 非空
        CE->>CE: 取 captured[-1] 作 result
        opt captured 多于1条
            CE->>CE: warnings 追加"多条 payload"提示
        end
        CE-->>C: 200 {status:ok, command, result, jobs_created, warnings}
    else captured 为空
        CE-->>C: 200 {status:ok, result:null, warnings:["no structured output"]}
    end
```

结果捕获机制细节：

- **线程局部缓冲**：`push_result_capture`/`pop_result_capture` 操作的是线程局部存储（`utils/output` 内部实现）。这意味着 Flask 多线程处理并发 `/command/exec` 请求时，每个请求的捕获缓冲互不干扰——线程 A 的 `pop_result_capture` 不会取到线程 B 的命令输出。
- **命令异常也入队**：`run_command` 抛异常时，`command_exec` 的 try 块捕获后主动调 `output_result(CommandResult(status='error', ...))`（[`agent_endpoints.py:98-104`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L98)），把错误塞进捕获缓冲。所以 `pop_result_capture` 总能拿到至少一条结果，`captured` 为空仅当命令本身未调 `output_result`（即未改造的人类模式命令）。
- **多条结果取最后一条**：一个命令可能多次调 `output_result`（如 `android hooking watch` 在 hook 命中时反复产出结果）。`command_exec` 取 `captured[-1]` 作 `result`，其余通过 warning 告知 Agent"命令产出了 N 条结构化 payload，只返回最后一条"（[`agent_endpoints.py:119-125`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L119)）。Agent 若需全部事件应改用 `/events/poll` 轮询。
- **`Repl()` 每请求新建**：`command_exec` 内 `repl = Repl()`（[`agent_endpoints.py:91`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L91)）每次请求新建 Repl 实例。Repl 构造较轻（只初始化 completer 与 PromptSession，PromptSession 不实际启动），新建避免跨请求状态污染。但 `Repl.run_command` 会调 `app_state.add_command_to_history`，所以命令历史是跨请求共享的（历史在全局 `app_state` 单例）。

## 📐 统一 JSON Schema 与端点响应结构（ASCII 框图）

下图展示所有端点返回的统一五字段 schema，以及不同端点如何填充各字段。

```
统一响应 schema (所有 agent_endpoints 端点):
┌──────────────────────────────────────────────────────────┐
│ {                                                        │
│   "status": "ok" | "error",                             │
│   "command": "<执行的命令或端点路径>",                   │
│   "result": <端点特定数据>,                             │
│   "jobs_created": [<本次创建的 Job uuid>],              │
│   "warnings": [<提示信息列表>]                          │
│ }                                                        │
└──────────────────────────────────────────────────────────┘

各端点填充:
┌─────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ 端点         │ status       │ command      │ result       │ jobs_created │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /command/exec│ ok/error    │ 用户命令串   │ CommandResult│ 命令产生的   │
│  (单命令)    │              │              │ .result      │ Job uuid 列表│
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /command/exec│ 数组, 每项   │ 每条命令     │ 每条的结果   │ 每条的       │
│  (多命令)    │ 同上         │              │              │ jobs_created │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /state       │ ok           │ "/state"     │ {connection, │ []           │
│              │              │              │  pid, jobs}  │              │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /events/poll │ ok           │ "/events/poll"│ {events,    │ []           │
│              │              │              │  dropped,...}│              │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /capabilities│ ok           │ "/capabilities"│{commands:  │ []           │
│              │              │              │  [...]}      │              │
├─────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ /agent/rpc/m │ ok / error   │ "/agent/rpc/m"│ RPC 原始返回│ []           │
│              │ (error→500)  │              │ 或 {error:}  │              │
└─────────────┴──────────────┴──────────────┴──────────────┴──────────────┘

错误响应 (无 agent, 通用):
┌──────────────────────────────────────────────────────────┐
│ status: 503 (无 agent) 或 500 (RPC 调用失败)             │
│ body: {                                                  │
│   "status": "error",                                    │
│   "command": "" 或 "/agent/rpc/<method>",               │
│   "result": {"error": "no agent is connected..."},      │
│   "jobs_created": [],                                    │
│   "warnings": []                                         │
│ }                                                        │
└──────────────────────────────────────────────────────────┘
```

Schema 设计要点：

- **`jobs_created` 字段的语义**：它记录本次命令执行过程中新创建的 Job uuid 列表，让 Agent 知道"这条命令产生了哪些可后续 kill 的 Job"。该字段由 `output_result` 在命令调用 `job_manager_state.add_job` 后填充——但当前实现中 `command_exec` 直接从 `captured` 取 `jobs_created`（[`agent_endpoints.py:119`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L119)），依赖命令实现主动在 `CommandResult` 里带上 `jobs_created`。未改造的命令该字段为空列表。
- **`warnings` 的用途**：非致命提示信息。典型场景：命令无结构化输出（`["command produced no structured output..."]`，[`agent_endpoints.py:114`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L114)）、命令产出多条 payload（`["command emitted N structured payloads..."]`，[`agent_endpoints.py:123`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L123)）。Agent 应把 warnings 反馈给用户但不视为失败。
- **`/command/exec` 的响应形态切换**：单命令返回对象，多命令返回数组（[`agent_endpoints.py:128-130`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L128)）。Agent 解析时需先检查 `isinstance(response, list)` 决定是单对象还是数组——这与 `/agent/rpc` 总是返回单对象不同，多命令批处理的响应形态是动态的。
- **`/agent/rpc` 的 `command` 字段保留原 method 名**：`command` 字段是 `/agent/rpc/{0}'.format(method)`（[`agent_endpoints.py:271`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L271)），用 URL 里的原始 method 名（未转 snake_case），便于 Agent 回溯是哪个 RPC 调用。但实际调用用的是 `to_snake_case(method)`（[`agent_endpoints.py:252`](https://github.com/android-security-engineer/objection-skills/blob/master/objection/api/agent_endpoints.py#L252)），所以 `command` 字段可能与实际方法名大小写不同。

## 🔄 与 /rpc/invoke 的端点选择决策

下图帮助 Agent 在 `/command/exec`、`/agent/rpc/<method>`、`/rpc/invoke/<method>` 三者间选择。

```mermaid
flowchart TD
    Q1{"需要执行 objection<br/>命令字符串?"}
    Q1 -->|是| CE["/command/exec<br/>复用人类命令逻辑"]
    Q1 -->|否| Q2{"需要统一 JSON schema<br/>与错误处理?"}

    Q2 -->|是| ARPC["/agent/rpc/<method><br/>统一 schema, JSON 数组参数"]
    Q2 -->|否| RINV["/rpc/invoke/<method><br/>原始响应, JSON 对象参数"]

    CE --> CE_NOTE["优点: 命令层全套逻辑<br/>缺点: 命令需已改造为 output_result"]
    ARPC --> ARPC_NOTE["优点: Agent 友好<br/>缺点: 需知道 RPC 方法名"]
    RINV --> RINV_NOTE["优点: 最薄桥接<br/>缺点: 朴素错误格式, 参数易错位"]
```

选择决策说明：

- **优先用 `/command/exec`**：Agent 应优先用命令字符串而非直接 RPC。命令层封装了参数解析、Job 管理、输出格式化、历史记录，且 `jobs_created` 让 Agent 能追踪副作用。只有当目标能力未被任何命令覆盖时才下沉到 RPC 层。
- **`/agent/rpc` 优于 `/rpc/invoke`**：当必须直接调 RPC 时，`/agent/rpc` 的统一 schema 与 JSON 数组参数更不易出错。`/rpc/invoke` 的 JSON 对象参数依赖字典有序，Agent 容易传错顺序。`/rpc/invoke` 适合已知 Frida RPC 返回结构、需要 `?json=false` 透传原始响应的场景。
- **`/capabilities` 前置调用**：Agent 在连接设备前应先调 `/capabilities` 了解可用命令，据此规划后续 `/command/exec` 调用。这是"先看能力再行动"的 Agent 工作流模式。

## 🔗 相关文档
- [整体架构](/guide/architecture)
- [HTTP API 端点](/guide/agent-http)
- [面向 AI Agent 使用](/guide/agent-usage)
- [统一 JSON Schema](/guide/agent-schema)
- [异步事件缓冲](/reference/utils/events)
- [统一输出层](/reference/utils/output)
- [HTTP 应用入口](/reference/api/app)
- [RPC 桥接](/reference/api/rpc)
