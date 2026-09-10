from typing import Optional

import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def get(args: list) -> Optional[CommandResult]:
    """
        Gets cookies using the iOS NSHTTPCookieStorage sharedHTTPCookieStorage
        and prints them to the screen.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    cookies = api.ios_cookies_get()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'cookies': cookies, 'count': len(cookies)}),
            command='ios cookies get',
        )

    if len(cookies) <= 0:
        click.secho('No cookies found')
        return None

    click.secho(tabulate(
        [[
            cookie['name'],
            cookie['value'],
            cookie['expiresDate'],
            cookie['domain'],
            cookie['path'],
            cookie['isSecure'],
            cookie['isHTTPOnly']
        ] for cookie in cookies], headers=['Name', 'Value', 'Expires', 'Domain', 'Path', 'Secure', 'HTTPOnly'],
    ))
    return None
