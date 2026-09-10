from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def android_proxy_set(args: list = None) -> Optional[CommandResult]:
    """
        Sets a proxy specifically within the application.

        :param args:
        :return:
    """

    if len(args) != 2:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'expected <ip address> <port>'},
                    status='error',
                    human_text='Usage: android proxy set <ip address> <port>',
                    exit_code=1,
                ),
                command='android proxy set',
            )
        click.secho('Usage: android proxy set <ip address> <port>', bold=True)
        return None

    api = state_connection.get_api()
    api.android_proxy_set(args[0], args[1])

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'proxy_set', 'host': args[0], 'port': args[1]}),
            command='android proxy set',
        )
    return None
