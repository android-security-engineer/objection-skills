from typing import Optional

import litecli
from litecli.main import LiteCli

from ..utils.output import CommandResult, output_result


def modify_config(rc):
    """
        Monkey patches the LiteCLI config to toggle
        settings that make more sense for us.

        :param rc:
        :return:
    """

    c = real_get_config(rc)
    c['main']['less_chatty'] = 'True'
    c['main']['enable_pager'] = 'False'

    return c


real_get_config = litecli.main.get_config
litecli.main.get_config = modify_config


def cleanup(p) -> None:
    """
        Remove a cached SQLite db

        :param p:
        :return:
    """

    os.remove(p)


def _should_sync_once_done(args: list) -> bool:
    """
        Checks if --sync flag was provided.

        :param args:
        :return:
    """

    return '--sync' in args


def connect(args: list) -> CommandResult:
    """
        Connects to a SQLite database by downloading a copy of the database
        from the device and storing it locally in a temporary directory.

        :param args:
        :return:
    """

    if len(args) <= 0:
        human_text = 'Usage: sqlite connect <remote_file> (optional: --sync)'
        return output_result(
            CommandResult(
                result={'error': 'missing remote file'},
                status='error',
                human_text=human_text,
            ),
            command='sqlite connect',
        )

    db_location = args[0]

    human_text = ('Use `filesystem download <remote_file> <local.sqlite>` '
                  'to pull the database, then inspect locally.')
    return output_result(
        CommandResult(
            result={'action': 'download_local_inspect', 'db_location': db_location},
            human_text=human_text,
            warnings=['The interactive litecli shell cannot run under an AI Agent.'],
        ),
        command='sqlite connect',
    )
