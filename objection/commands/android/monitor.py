from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def string_canary(args: list) -> Optional[CommandResult]:
    """
        Monitors for a string canary argument and reports when
        it is found.

        :param args:
        :return:
    """

    if len(args) < 1:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing canary value'},
                    status='error',
                    human_text='Usage: android monitor canary <value> (optional: <filter>)',
                    exit_code=1,
                ),
                command='android monitor canary',
            )
        click.secho('Usage: android monitor canary <value> (optional: <filter>)', bold=True)
        return None

    target_class = args[0]

    api = state_connection.get_api()
    api.android_live_print_class_instances(target_class)

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'monitoring_canary', 'value': target_class},
                warnings=['Canary hits arrive as async messages; poll via `agent state` or HTTP /events.',
                          'Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android monitor canary',
        )
    return None
