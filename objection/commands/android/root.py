from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def disable(args: list = None) -> CommandResult:
    """
        Performs a generic anti root detection.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_root_detection_disable()

    return output_result(
        CommandResult(
            result={'action': 'root_detection_disabled'},
            human_text='Root detection disabled',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android root disable',
    )


def simulate(args: list = None) -> CommandResult:
    """
        Simulate a rooted environment.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_root_detection_enable()

    return output_result(
        CommandResult(
            result={'action': 'root_detection_simulated'},
            human_text='Root detection simulated',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android root simulate',
    )
