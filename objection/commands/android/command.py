from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def execute(args: list) -> Optional[CommandResult]:
    """
        Runs a shell command on an Android device.

        :param args:
        :return:
    """

    command = ' '.join(args)
    json_mode = should_output_json(args)
    if not json_mode:
        click.secho('Running shell command: {0}\n'.format(command), dim=True)

    api = state_connection.get_api()
    response = api.android_shell_exec(command)

    stdout = response.get('stdOut', '') if isinstance(response, dict) else ''
    stderr = response.get('stdErr', '') if isinstance(response, dict) else ''

    if not json_mode:
        if 'stdOut' in response and len(response['stdOut']) > 0:
            click.secho(response['stdOut'], bold=True)

        if 'stdErr' in response and len(response['stdErr']) > 0:
            click.secho(response['stdErr'], bold=True, fg='red')

    if json_mode:
        return output_result(
            CommandResult(result={'command': command, 'stdout': stdout, 'stderr': stderr}),
            command='android shell_exec',
        )
    return None
