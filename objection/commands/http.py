from typing import Optional

import click

from ..commands.filemanager import pwd
from ..state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def start(args: list) -> Optional[CommandResult]:
    """
        Start's an http server, exposing the mobile devices filesystem.

        :param args:
        :return:
    """

    port = 9000

    if len(args) > 0:
        port = int(args[0])

    click.secho('Starting server on port {port}...'.format(port=port), dim=True)

    api = state_connection.get_api()
    api.http_server_start(pwd(), port)

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'http_start', 'port': port, 'root': pwd()}),
            command='http start',
        )
    return None


def stop(args: list) -> Optional[CommandResult]:
    """
        Stops the on device HTTP server

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.http_server_stop()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'http_stop'}),
            command='http stop',
        )
    return None


def status(args: list) -> Optional[CommandResult]:
    """
        Get the status of the HTTP server

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.http_server_status()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'http_status'}),
            command='http status',
        )
    return None
