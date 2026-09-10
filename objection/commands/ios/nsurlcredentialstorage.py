from typing import Optional

import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def dump(args: list = None) -> Optional[CommandResult]:
    """
        Dumps credentials stored in NSURLCredentialStorage

        :param args:
        :return:
    """

    api = state_connection.get_api()
    cookies = api.ios_credential_storage()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'credentials': cookies, 'count': len(cookies)}),
            command='ios nsurlcredentialstorage dump',
        )

    human_lines = tabulate(
        [[
            entry['protocol'],
            entry['host'],
            entry['port'],
            entry['authMethod'].replace('NSURLAuthenticationMethod', ''),
            entry['user'],
            entry['password'],
        ] for entry in cookies], headers=[
            'Protocol', 'Host', 'Port', 'Authentication Method', 'User', 'Password'
        ],
    )
    return output_result(
        CommandResult(result={'credentials': cookies, 'count': len(cookies)}, human_text=human_lines),
        command='ios nsurlcredentialstorage dump',
    )
