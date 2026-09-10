from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json
from ..state.device import device_state, Ios, Android


def alert(args: list = None) -> Optional[CommandResult]:
    """
        Displays an alert message via a popup or a Toast message
        on the mobile device.

        :param args:
        :return:
    """

    if len(args) <= 0:
        message = 'objection!'
    else:
        message = args[0]

    if isinstance(device_state.platform, Ios):
        _alert_ios(message)

    if isinstance(device_state.platform, Android):
        pass

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'alert', 'message': message, 'platform': str(device_state.platform)}),
            command='ui alert',
        )
    return None


def _alert_ios(message: str):
    """
        Display an alert on iOS

        :param message:
        :return:
    """

    api = state_connection.get_api()
    api.ios_ui_alert(message)


def ios_screenshot(args: list = None) -> Optional[CommandResult]:
    """
        Take an iOS screenshot.

        :param args:
        :return:
    """

    if len(args) <= 0:
        click.secho('Usage: ios ui screenshot <local png destination>', bold=True)
        if should_output_json(args):
            return output_result(
                CommandResult(status='error', result={'error': 'missing local png destination'}),
                command='ios ui screenshot',
            )
        return None

    destination = args[0]

    if not destination.endswith('.png'):
        destination = destination + '.png'

    api = state_connection.get_api()
    png = api.ios_ui_screenshot()

    with open(destination, 'wb') as f:
        f.write(png)

    click.secho('Screenshot saved to: {0}'.format(destination), fg='green')

    if should_output_json(args):
        return output_result(
            CommandResult(result={'saved_to': destination, 'bytes': len(png)}),
            command='ios ui screenshot',
        )
    return None


def dump_ios_ui(args: list = None) -> Optional[CommandResult]:
    """
        Dumps the current iOS user interface in a serialized form.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ui = api.ios_ui_window_dump()

    if not should_output_json(args):
        click.secho(ui)

    if should_output_json(args):
        return output_result(
            CommandResult(result={'ui': ui}),
            command='ios ui dump',
        )
    return None


def bypass_touchid(args: list = None) -> Optional[CommandResult]:
    """
        Starts a new objection job that hooks into the iOS TouchID
        classes, replacing the verification logic to always pass.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_ui_biometrics_bypass()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'bypass_touchid'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios ui bypass_touchid',
        )
    return None


def android_screenshot(args: list = None) -> Optional[CommandResult]:
    """
        Take an Android screenshot.

        :param args:
        :return:
    """

    if len(args) <= 0:
        click.secho('Usage: android ui screenshot <local png destination>', bold=True)
        if should_output_json(args):
            return output_result(
                CommandResult(status='error', result={'error': 'missing local png destination'}),
                command='android ui screenshot',
            )
        return None

    # add the .png extension if it does not already exist
    destination = args[0] if args[0].endswith('.png') else args[0] + '.png'

    # download the file
    api = state_connection.get_api()
    data = api.android_ui_screenshot()

    image = bytearray(map(lambda x: x % 256, data))

    with open(destination, 'wb') as f:
        f.write(image)

    click.secho('Screenshot saved to: {0}'.format(destination), fg='green')

    if should_output_json(args):
        return output_result(
            CommandResult(result={'saved_to': destination, 'bytes': len(image)}),
            command='android ui screenshot',
        )
    return None


def android_flag_secure(args: list = None) -> Optional[CommandResult]:
    """
        Control FLAG_SECURE of the current Activity, allowing or disallowing
        the use of hardware key combinations and screencap to take screenshots.

        :param args:
        :return:
    """

    if len(args) <= 0 or args[0] not in ('true', 'false'):
        click.secho('Usage: android ui FLAG_SECURE <true/false>', bold=True)
        if should_output_json(args):
            return output_result(
                CommandResult(status='error', result={'error': 'flag must be true or false'}),
                command='android ui flag_secure',
            )
        return None

    api = state_connection.get_api()
    api.android_ui_set_flag_secure(args[0])

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'set_flag_secure', 'value': args[0]}),
            command='android ui flag_secure',
        )
    return None
