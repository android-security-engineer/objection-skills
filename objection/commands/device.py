import click
from tabulate import tabulate
from typing import Optional

from ..state.connection import state_connection
from ..state.device import device_state, Android, Ios
from ..utils.output import CommandResult, output_result, should_output_json


def get_environment(args: list = None) -> Optional[CommandResult]:
    """
        Get information about the current environment.

        This method will call the correct runtime specific
        method to get the information that it can.

        :param args:
        :return:
    """

    if device_state.platform == Ios:
        return _get_ios_environment(args)

    if device_state.platform == Android:
        return _get_android_environment(args)

    return None


def _get_ios_environment(args: list = None) -> Optional[CommandResult]:
    """
        Prints information about the iOS environment.

        This includes the current OS version as well as directories
        of interest for the current applications Documents, Library and
        main application bundle.

        :return:
    """

    paths = state_connection.get_api().env_ios_paths()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'platform': 'ios', 'paths': paths}),
            command='env',
        )

    click.secho('')
    click.secho(tabulate(paths.items(), headers=['Name', 'Path']))
    return None


def _get_android_environment(args: list = None) -> Optional[CommandResult]:
    """
        Prints information about the Android environment.

        :return:
    """

    paths = state_connection.get_api().env_android_paths()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'platform': 'android', 'paths': paths}),
            command='env',
        )

    click.secho('')
    click.secho(tabulate(paths.items(), headers=['Name', 'Path']))
    return None
