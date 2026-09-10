from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def monitor(args: list = None) -> Optional[CommandResult]:
    """
        Starts a new objection job that monitors the Android clipboard
        and reports on new strings found.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_monitor_clipboard()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'monitoring_clipboard'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                          'New clipboard strings arrive as async messages.'],
            ),
            command='android clipboard monitor',
        )
    return None
