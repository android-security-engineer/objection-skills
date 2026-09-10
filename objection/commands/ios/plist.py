import os
from typing import Optional
import click

from objection.commands import filemanager
from objection.state.connection import state_connection
from objection.state.device import device_state
from objection.utils.helpers import is_unix_absolute_path
from objection.utils.output import CommandResult, output_result, should_output_json


def cat(args: list = None) -> Optional[CommandResult]:
    """
        Parses a plist on an iOS device and echoes it in a more human
        readable way.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing plist path'},
                status='error',
                human_text='Usage: ios plist cat <remote_plist>',
                exit_code=1,
            ),
            command='ios plist cat',
        )

    plist = args[0]

    if not is_unix_absolute_path(plist):
        pwd = filemanager.pwd()
        plist = device_state.platform.path_separator.join([pwd, plist])

    api = state_connection.get_api()
    plist_data = api.ios_plist_read(plist)

    return output_result(
        CommandResult(result={'path': plist, 'data': plist_data}, human_text=str(plist_data)),
        command='ios plist cat',
    )
