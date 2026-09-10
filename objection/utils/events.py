"""
    objection.utils.events
    ~~~~~~~~~~~~~~~~~~~~~~~

    异步事件缓冲，供 AI Agent / HTTP API 拉取。

    objection 的 Hook 命中、Job 注册等异步结果通过 Frida 的 ``script.on('message')``
    回调到达（见 :func:`objection.utils.agent.OutputHandlers.script_on_message`）。
    人类模式下这些消息直接打印到终端；但对 AI Agent，需要一个可轮询的缓冲区，
    以便 ``GET /events/poll`` 或 ``agent state`` 取回。

    设计：一个进程内全局有界队列。``record_event`` 入队，``drain_events`` 取出并清空。
    队列有上限以防失控的 Hook 风暴耗尽内存——溢出时丢弃最旧的事件并记录 dropped 计数。
"""

from collections import deque
from threading import Lock

from .output import is_json_output

# 有界队列：保留最近 N 条事件。Hook 风暴时丢弃最旧的。
_MAX_EVENTS = 1000

_events: deque = deque(maxlen=_MAX_EVENTS)
_lock = Lock()
_dropped = 0


def record_event(message: dict, data=None) -> None:
    """
        记录一条来自 agent 的异步消息。

        仅在 JSON 输出模式下记录——人类模式消息已直接打印，无需重复缓冲。

        :param message: Frida 消息字典（含 ``payload`` 等）。
        :param data: 二进制伴随数据（通常忽略）。
    """

    global _dropped

    if not is_json_output():
        return

    with _lock:
        if len(_events) == _events.maxlen:
            _dropped += 1
        _events.append({
            'message': message,
            'data': data.decode('utf-8', 'replace') if isinstance(data, (bytes, bytearray)) else data,
        })


def drain_events() -> dict:
    """
        取出并清空所有缓冲事件。

        :return: ``{'events': [...], 'dropped': <int>, 'remaining': 0}``。
    """

    global _dropped

    with _lock:
        events = list(_events)
        _events.clear()
        dropped = _dropped
        _dropped = 0

    return {
        'events': events,
        'dropped': dropped,
        'remaining': 0,
    }


def peek_events() -> dict:
    """
        查看缓冲事件（不清空）。

        :return: ``{'events': [...], 'dropped': <int>, 'remaining': <int>}``。
    """

    with _lock:
        return {
            'events': list(_events),
            'dropped': _dropped,
            'remaining': len(_events),
        }
