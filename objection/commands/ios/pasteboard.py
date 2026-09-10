from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def monitor(args: list = None) -> Optional[CommandResult]:
    """
        Starts a new objection job that monitors the iOS pasteboard
        and reports on new strings found.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_monitor_pasteboard()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'monitoring_pasteboard'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                          'New pasteboard strings arrive as async messages.'],
            ),
            command='ios pasteboard monitor',
        )
    return None
