from typing import Optional

import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def info(args: list) -> Optional[CommandResult]:
    """
        Gets information about binaries and frameworks.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    binary_info = api.ios_binary_info()

    if not should_output_json(args):
        click.secho(tabulate(
            [[
                name,
                information['type'],
                information['encrypted'],
                information['pie'],
                information['arc'],
                information['canary'],
                information['stackExec'],
                information['rootSafe']
            ] for name, information in binary_info.items()],
            headers=['Name', 'Type', 'Encrypted', 'PIE', 'ARC', 'Canary', 'Stack Exec', 'RootSafe'],
        ))

    if should_output_json(args):
        return output_result(
            CommandResult(result={'binaries': binary_info, 'count': len(binary_info)}),
            command='ios binary info',
        )
    return None
