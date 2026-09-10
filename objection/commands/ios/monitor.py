from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def crypto_enable(args: list = None) -> Optional[CommandResult]:
    """
        Attempts to enable ios crypto monitoring.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_monitor_crypto_enable()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'crypto_monitoring_enabled'},
                warnings=['Crypto events arrive as async messages; poll via `agent state` or HTTP /events.',
                          'Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios monitor crypto',
        )
    return None
