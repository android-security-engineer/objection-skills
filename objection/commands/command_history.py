import os
from typing import Optional

from ..state.app import app_state
from objection.utils.output import CommandResult, output_result, should_output_json


def history(args: list) -> Optional[CommandResult]:
    """
        Lists the commands that have been run in the current session.

        :param args:
        :return:
    """

    if should_output_json(args):
        return output_result(
            CommandResult(result={'commands': app_state.successful_commands,
                                  'count': len(app_state.successful_commands)}),
            command='commands history',
        )

    human_text = 'Unique commands run in current session:\n' + '\n'.join(app_state.successful_commands)
    return output_result(
        CommandResult(result={'commands': app_state.successful_commands,
                              'count': len(app_state.successful_commands)}, human_text=human_text),
        command='commands history',
    )


def save(args: list) -> Optional[CommandResult]:
    """
        Save the current sessions command history to a file.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(status='error', result={'error': 'missing local destination'},
                          human_text='Usage: commands save <local destination>'),
            command='commands save',
        )

    destination = os.path.expanduser(args[0]) if args[0].startswith('~') else args[0]

    with open(destination, 'w') as f:
        for command in app_state.successful_commands:
            f.write('{0}\n'.format(command))

    return output_result(
        CommandResult(result={'saved_to': destination, 'count': len(app_state.successful_commands)},
                      human_text='Saved commands to: {0}'.format(destination)),
        command='commands save',
    )


def clear(args: list) -> Optional[CommandResult]:
    """
        Clears the current sessions command history.

        :param args:
        :return:
    """

    app_state.clear_command_history()
    return output_result(
        CommandResult(result={'cleared': True}, human_text='Command history cleared.'),
        command='commands clear',
    )
