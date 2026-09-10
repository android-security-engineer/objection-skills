"""
    objection.console.agent_cli
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    面向 AI Agent 的 CLI 子命令组（``objection agent ...``）。

    与面向人类的 ``objection run`` / REPL 不同，这组命令：
        - 强制结构化 JSON 输出（统一 schema，见 objection.utils.output）
        - 提供状态查询与能力自描述，便于 Agent 决策
        - 可直调 agent RPC，绕过人类命令层

    设计动机：AI Agent 用工具需要 JSON 进 / JSON 出、可解析、可发现能力，
    而人类命令输出是彩色文本。这组命令是 Agent 的原生入口。
"""

import json
from typing import Optional

import click

from objection.state.app import app_state
from objection.state.connection import state_connection
from objection.state.jobs import job_manager_state
from objection.utils.helpers import to_snake_case
from objection.utils.output import CommandResult, output_result, set_json_output
from .commands import COMMANDS
from .repl import Repl


def _bootstrap_agent():
    """
        准备 agent 会话：注入 agent、设置全局 JSON 输出。

        ``agent`` 子命令组里大多数命令需要已连接的 agent。该辅助函数
        复用 ``cli.get_agent`` 的逻辑，但置于本模块以避免循环导入。

        :return:
    """

    from .cli import get_agent

    set_json_output(True)
    agent = get_agent()
    state_connection.set_agent(agent=agent)
    return agent


@click.group()
def agent() -> None:
    """
        面向 AI Agent 的子命令组。所有子命令默认输出 JSON。

        典型 Agent 工作流：
            1. ``agent capabilities`` —— 发现可用命令与参数
            2. ``agent exec "<command>"`` —— 执行一条 objection 命令，拿 JSON 结果
            3. ``agent state`` —— 查询当前连接 / Job / Hook 状态
            4. ``agent rpc <method> [--args ...]`` —— 直调底层 agent RPC
    """


@agent.command('exec')
@click.argument('command', nargs=-1, required=True)
@click.option('--no-spawn', 'spawn', is_flag=True, default=False,
              help='Do not spawn the target; attach only.')
def agent_exec(command: tuple, spawn: bool) -> None:
    """
        执行一条 objection 命令，返回统一 JSON 结果。

        COMMAND 是 objection 命令字符串（同 REPL），例如：
            objection -g com.x agent exec 'android hooking list classes'

        会话复用：本命令会 attach/spawn 目标并注入 agent，执行后保持会话。
        连续的 ``agent exec`` 调用若在同一进程内，会复用已建立的 agent。
    """

    try:
        _bootstrap_agent()
    except Exception as e:
        output_result(
            CommandResult(
                result={'error': 'failed to bootstrap agent: {0}'.format(e)},
                status='error',
                human_text='Failed to connect: {0}'.format(e),
                exit_code=1,
            ),
            command='agent exec',
        )
        return

    command_str = ' '.join(command)
    repl = Repl()

    # run_command 会把命令分派到对应实现；因为我们已 set_json_output(True)，
    # 已改造的命令会走 JSON 输出路径，未改造的命令仍打印人类文本（Agent 可据此判断）
    try:
        repl.run_command(command_str)
    except Exception as e:
        output_result(
            CommandResult(
                result={'error': str(e)},
                status='error',
                human_text='Command failed: {0}'.format(e),
                exit_code=1,
            ),
            command=command_str,
        )


@agent.command('rpc')
@click.argument('method')
@click.option('--args', 'args_json', default=None,
              help='JSON array of positional arguments for the RPC method.')
def agent_rpc(method: str, args_json: Optional[str]) -> None:
    """
        直调 agent 的一个 RPC 方法（绕过人类命令层），返回原始结构化数据。

        METHOD 是 agent rpc.exports 中的方法名（蛇形或驼峰均可），例如：
            objection -g com.x agent rpc android_hooking_get_classes
            objection -g com.x agent rpc android_keystore_list

        --args 为 JSON 数组，作为方法的位置参数。
    """

    try:
        _bootstrap_agent()
    except Exception as e:
        output_result(
            CommandResult(
                result={'error': 'failed to bootstrap agent: {0}'.format(e)},
                status='error',
                exit_code=1,
            ),
            command='agent rpc',
        )
        return

    api = state_connection.get_api()
    method_name = to_snake_case(method)

    args_list = []
    if args_json:
        try:
            args_list = json.loads(args_json)
            if not isinstance(args_list, list):
                raise ValueError('--args must be a JSON array')
        except (json.JSONDecodeError, ValueError) as e:
            output_result(
                CommandResult(
                    result={'error': 'invalid --args: {0}'.format(e)},
                    status='error',
                    exit_code=1,
                ),
                command='agent rpc {0}'.format(method),
            )
            return

    try:
        fn = getattr(api, method_name, None)
        if fn is None:
            raise AttributeError('unknown RPC method: {0}'.format(method_name))
        result = fn(*args_list)
        output_result(
            CommandResult(result=result),
            command='agent rpc {0}'.format(method),
        )
    except Exception as e:
        output_result(
            CommandResult(
                result={'error': str(e)},
                status='error',
                exit_code=1,
            ),
            command='agent rpc {0}'.format(method),
        )


@agent.command('state')
def agent_state() -> None:
    """
        输出当前会话状态 JSON：连接信息、设备、运行中的 Job。

        供 Agent 在多步流程中感知"我现在连了什么、装了哪些 Hook/Job"。
    """

    try:
        _bootstrap_agent()
    except Exception as e:
        output_result(
            CommandResult(
                result={'error': 'failed to bootstrap agent: {0}'.format(e)},
                status='error',
                exit_code=1,
            ),
            command='agent state',
        )
        return

    sc = state_connection
    agent_obj = sc.get_agent() if sc.agent else None

    # 收集运行中的 Job（Python 侧 job_manager_state）
    jobs = []
    try:
        for j in job_manager_state.jobs:
            jobs.append({
                'identifier': getattr(j, 'identifier', None),
                'name': getattr(j, 'name', None) or getattr(j, 'type', None),
            })
    except Exception:
        pass

    state = {
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
    output_result(CommandResult(result=state), command='agent state')


@agent.command('capabilities')
def agent_capabilities() -> None:
    """
        枚举所有可用命令及其结构，供 Agent 自发现能力。

        不需要连接设备——这是命令注册表的静态快照。
    """

    # capabilities 不连设备，但 agent 组强制 JSON 输出，故显式置位
    set_json_output(True)

    capabilities = _enumerate_capabilities(COMMANDS)
    output_result(
        CommandResult(result={'commands': capabilities}),
        command='agent capabilities',
    )


def _enumerate_capabilities(commands: dict, prefix: str = '') -> list:
    """
        递归遍历 COMMANDS 注册表，输出扁平的命令列表。

        :param commands: COMMANDS 子树。
        :param prefix: 命令前缀（如 'android hooking'）。
        :return: [{name, meta, has_exec, subcommands}] 列表。
    """

    result = []
    for name, node in commands.items():
        if not isinstance(node, dict):
            continue

        full = '{0} {1}'.format(prefix, name).strip() if prefix else name
        meta = node.get('meta', '')
        has_exec = 'exec' in node and callable(node.get('exec'))

        entry = {
            'name': full,
            'meta': meta,
            'has_exec': has_exec,
        }

        sub_commands = node.get('commands', {})
        if sub_commands:
            entry['subcommands'] = _enumerate_capabilities(sub_commands, full)

        result.append(entry)

    return result
