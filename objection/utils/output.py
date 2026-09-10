"""
    objection.utils.output
    ~~~~~~~~~~~~~~~~~~~~~~

    统一的命令输出渲染层。

    设计目的：
        objection 的命令函数传统上直接 ``click.secho`` 打印人类可读文本，
        这对交互式用户友好，但对 AI Agent / 脚本不友好（无法可靠解析）。

        本模块引入 ``CommandResult`` 结构化结果对象。命令函数返回它，
        由 :func:`output_result` 根据当前输出模式决定渲染成：
            - JSON（``--json`` 或 ``app_state.json_output`` 时）—— 供 Agent 解析
            - 人类文本（默认）—— 保留原有体验

    统一 JSON schema：
        {
            "status": "ok" | "error",
            "command": "<触发命令>",
            "result": <任意结构化数据>,
            "jobs_created": [<int>, ...],
            "warnings": ["<str>", ...]
        }
"""

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Optional

import click

from ..state.app import app_state


# ---------------------------------------------------------------------------
# 结果捕获机制
#
# 用于 HTTP API 等非 stdout 场景：注册一个捕获器后，output_result() 在 JSON
# 模式下不再 click.echo，而是把 payload append 到捕获器，供调用方取回。
# 这让改造后的命令（已走 output_result）无需改动即可服务于 HTTP 端点。
# ---------------------------------------------------------------------------

_capture_stack: list = []


def push_result_capture() -> list:
    """
        开启一次结果捕获。返回一个新的捕获缓冲区。

        在捕获期间，output_result() 的 JSON 输出会被追加到该缓冲区而非
        打印到 stdout。调用方负责调用 :func:`pop_result_capture` 结束捕获。

        :return: 捕获缓冲区（list）。
    """

    buf = []
    _capture_stack.append(buf)
    return buf


def pop_result_capture() -> Optional[list]:
    """
        结束最近一次结果捕获，返回其缓冲区。

        :return: 捕获缓冲区，若栈为空则 None。
    """

    if not _capture_stack:
        return None
    return _capture_stack.pop()


def _capturing() -> bool:
    """ 当前是否处于结果捕获中。 """

    return bool(_capture_stack)


@dataclass
class CommandResult:
    """
        一个命令执行后的结构化结果。

        命令函数应构造此对象并返回，而非直接打印。
        :func:`output_result` 负责根据输出模式渲染。

        :param result: 命令的核心结构化输出（list/dict/scalar）。
        :param status: "ok" 或 "error"。
        :param human_text: 人类可读文本。为 None 时，JSON 模式输出 result，
                           人类模式下若提供则直接打印、否则回退到 result 的 repr。
        :param jobs_created: 本次命令创建的 Job identifier 列表（供 Agent 跟踪）。
        :param warnings: 非致命警告字符串列表。
        :param exit_code: 进程退出码（0 成功，非 0 失败）。
    """

    result: Any = None
    status: str = 'ok'
    human_text: Optional[str] = None
    jobs_created: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    exit_code: int = 0

    def to_dict(self, command: str = '') -> dict:
        """ 序列化为统一 JSON schema 字典。 """

        return {
            'status': self.status,
            'command': command,
            'result': self.result,
            'jobs_created': self.jobs_created,
            'warnings': self.warnings,
        }


def is_json_output() -> bool:
    """
        当前是否应输出 JSON。

        由全局 ``app_state.json_output`` 控制（CLI ``--json`` / ``agent exec``
        会置位），或命令级 ``--json`` 参数。

        :return:
    """

    return getattr(app_state, 'json_output', False)


def output_result(result: CommandResult, command: str = '') -> int:
    """
        渲染一个 CommandResult。

        JSON 模式下，打印统一 schema 的 JSON 到 stdout，并返回退出码；
        人类模式下，打印 ``human_text``（若有）或 result 的可读形式。

        :param result: 命令结果对象。
        :param command: 触发该结果的命令字符串（用于 JSON schema 的 command 字段）。
        :return: 退出码（0 成功，非 0 失败）。
    """

    if is_json_output():
        payload = result.to_dict(command)
        # 捕获模式（HTTP API 等）：交由调用方取回，不打印
        if _capturing():
            _capture_stack[-1].append(payload)
            return result.exit_code
        click.echo(json.dumps(payload, ensure_ascii=False, default=str, indent=2))
        return result.exit_code

    # 人类模式
    if result.warnings:
        for w in result.warnings:
            click.secho('Warning: {0}'.format(w), fg='yellow')

    if result.human_text is not None:
        click.echo(result.human_text)
    elif result.result is not None:
        # 没有专门的人类文本时，回退到结构化数据的可读形式
        click.echo(json.dumps(result.result, ensure_ascii=False, default=str, indent=2))

    return result.exit_code


def error_result(message: str, command: str = '', exit_code: int = 1) -> CommandResult:
    """
        快捷构造一个错误结果。

        :param message: 错误信息。
        :param command: 命令字符串。
        :param exit_code: 退出码。
        :return:
    """

    return CommandResult(
        result={'error': message},
        status='error',
        human_text=message,
        exit_code=exit_code,
    )


def should_output_json(args: Optional[list] = None) -> bool:
    """
        检查命令级 ``--json`` 标志或全局 JSON 模式。

        命令函数可用此判断是否需要准备结构化数据（即便渲染由
        :func:`output_result` 统一完成，某些命令在 JSON 模式下会跳过
        人类专用的表格渲染）。

        :param args: 命令参数列表。
        :return:
    """

    if is_json_output():
        return True

    if args and '--json' in args:
        return True

    return False


def emit_event(event_type: str, data: Any = None) -> None:
    """
        发射一个异步事件到输出流。

        用于 Hook 命中、Job 注册等需要"推送"给 Agent 的场景。
        JSON 模式下作为单独的 JSON 行打印（每行一个事件，便于 Agent 流式解析）；
        人类模式下走原有 ``send()`` 消息通道（由 agent 触发）。

        :param event_type: 事件类型，如 "hook_invocation"、"job_registered"。
        :param data: 事件数据。
    """

    if not is_json_output():
        return  # 人类模式由 agent 侧 send() 处理，这里不重复

    event = {
        'event': event_type,
        'data': data,
    }
    # 单行 JSON，写到 stdout，Agent 可按行解析事件流
    click.echo(json.dumps(event, ensure_ascii=False, default=str), flush=True)


def set_json_output(enabled: bool) -> None:
    """
        设置全局 JSON 输出模式。

        :param enabled:
    """

    app_state.json_output = enabled
