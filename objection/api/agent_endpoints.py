"""
    objection.api.agent_endpoints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    面向 AI Agent 的 HTTP API 端点。

    与 ``/rpc/invoke`` 直接桥接 Frida RPC 不同，这组端点工作在 objection 命令层，
    复用统一输出层 (:mod:`objection.utils.output`)，返回统一 JSON schema。

    端点：
        - ``POST /command/exec``  执行一条 objection 命令字符串，返回统一 JSON 结果
        - ``GET  /state``         连接 / 设备 / Job 状态快照
        - ``GET  /events/poll``   拉取并清空异步事件缓冲（Hook 命中等）
        - ``GET  /capabilities``  枚举可用命令（静态注册表快照，无需设备）
        - ``GET  /agent/rpc/<method>``  直调 agent RPC（与 /rpc/invoke 互补，强制 JSON）

    这些端点假定 objection 进程已通过 ``objection api`` 或 ``objection start --enable-api``
    注入了 agent（HTTP 服务器与 agent 共进程）。
"""

import json

from flask import Blueprint, jsonify, request, abort

from objection.state.connection import state_connection
from objection.state.jobs import job_manager_state
from objection.utils.events import drain_events
from objection.utils.helpers import to_snake_case
from objection.utils.output import (
    CommandResult, output_result, push_result_capture, pop_result_capture,
    set_json_output, is_json_output,
)

bp = Blueprint('agent_api', __name__, url_prefix='')


def _ensure_json_mode():
    """ HTTP Agent 端点强制 JSON 输出模式。 """

    if not is_json_output():
        set_json_output(True)


def _no_agent_response():
    """ 未注入 agent 时的统一错误响应。 """

    return jsonify({
        'status': 'error',
        'command': '',
        'result': {'error': 'no agent is connected; start objection with `objection api` first'},
        'jobs_created': [],
        'warnings': [],
    }), 503


@bp.route('/command/exec', methods=('POST',))
def command_exec():
    """
        执行一条 objection 命令字符串，返回统一 JSON 结果。

        请求体（JSON）::

            {"command": "android hooking list classes"}

        或多个命令::

            {"commands": ["android hooking list classes", "ios keychain dump"]}

        响应为统一 schema 的 JSON 对象（单命令）或数组（多命令）。
    """

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

    # 延迟导入，避免循环依赖（repl 依赖 cli，cli 依赖 agent_cli）
    from objection.console.repl import Repl
    repl = Repl()

    results = []
    for cmd in commands:
        buf = push_result_capture()
        try:
            repl.run_command(cmd)
        except Exception as e:
            # 命令抛异常时构造一个错误结果入队
            output_result(
                CommandResult(result={'error': str(e)}, status='error',
                              human_text='Command failed: {0}'.format(e), exit_code=1),
                command=cmd,
            )
        captured = pop_result_capture() or []

        if not captured:
            # 未改造的命令没有产生结构化结果——告知 Agent
            results.append({
                'status': 'ok',
                'command': cmd,
                'result': None,
                'jobs_created': [],
                'warnings': ['command produced no structured output; it may be unconverted or interactive-only.'],
            })
        else:
            # 一个命令通常产生一条结果；若有多条，取最后一条作为该命令的结果，
            # 其余作为附加事件。
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


@bp.route('/state', methods=('GET',))
def state():
    """
        返回当前会话状态：连接信息、设备、运行中的 Job。

        供 Agent 在多步流程中感知"现在连了什么、装了哪些 Hook/Job"。
    """

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
            jobs.append({
                'id': uuid,
                'type': job.job_type,
                'name': job.name,
            })
    except Exception:
        pass

    state_data = {
        'connection': {
            'type': sc.device_type,
            'network': sc.network,
            'host': sc.host,
            'port': sc.port,
            'device_id': sc.device_id,
            'name': sc.name,
            'spawn': sc.spawn,
            'foremost': sc.foremost,
        },
        'pid': getattr(agent_obj, 'pid', None) if agent_obj else None,
        'jobs': jobs,
    }
    return jsonify({
        'status': 'ok',
        'command': '/state',
        'result': state_data,
        'jobs_created': [],
        'warnings': [],
    })


@bp.route('/events/poll', methods=('GET',))
def events_poll():
    """
        拉取并清空异步事件缓冲。

        Hook 命中、canary 触发、pasteboard 变化等异步结果会缓冲在此。
        Agent 应在执行动作命令（如 ``android hooking watch``）后周期性轮询此端点。

        查询参数 ``?peek=1`` 仅查看不清空。
    """

    _ensure_json_mode()

    if 'peek' in request.args:
        from objection.utils.events import peek_events
        data = peek_events()
    else:
        data = drain_events()

    return jsonify({
        'status': 'ok',
        'command': '/events/poll',
        'result': data,
        'jobs_created': [],
        'warnings': [],
    })


@bp.route('/capabilities', methods=('GET',))
def capabilities():
    """
        枚举所有可用命令及其结构，供 Agent 自发现能力。

        不需要设备连接——这是命令注册表的静态快照。
    """

    _ensure_json_mode()

    from objection.console.commands import COMMANDS
    from objection.console.agent_cli import _enumerate_capabilities

    caps = _enumerate_capabilities(COMMANDS)
    return jsonify({
        'status': 'ok',
        'command': '/capabilities',
        'result': {'commands': caps},
        'jobs_created': [],
        'warnings': [],
    })


@bp.route('/agent/rpc/<string:method>', methods=('GET', 'POST'))
def agent_rpc(method):
    """
        直调 agent 的一个 RPC 方法，返回原始结构化数据。

        GET 请求无参数；POST 请求体为 JSON 数组，作为方法的位置参数::

            POST /agent/rpc/android_hooking_watch
            ["com.example!method", false, false, false]
    """

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
            'status': 'error',
            'command': '/agent/rpc/{0}'.format(method),
            'result': {'error': str(e)},
            'jobs_created': [],
            'warnings': [],
        }), 500

    return jsonify({
        'status': 'ok',
        'command': '/agent/rpc/{0}'.format(method),
        'result': result,
        'jobs_created': [],
        'warnings': [],
    })
