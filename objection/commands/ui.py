from typing import Optional

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

    return output_result(
        CommandResult(result={'action': 'alert', 'message': message, 'platform': str(device_state.platform)},
                      human_text='Alert displayed: {0}'.format(message)),
        command='ui alert',
    )


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
        return output_result(
            CommandResult(status='error', result={'error': 'missing local png destination'},
                          human_text='Usage: ios ui screenshot <local png destination>'),
            command='ios ui screenshot',
        )

    destination = args[0]

    if not destination.endswith('.png'):
        destination = destination + '.png'

    api = state_connection.get_api()
    png = api.ios_ui_screenshot()

    with open(destination, 'wb') as f:
        f.write(png)

    return output_result(
        CommandResult(result={'saved_to': destination, 'bytes': len(png)},
                      human_text='Screenshot saved to: {0}'.format(destination)),
        command='ios ui screenshot',
    )


def dump_ios_ui(args: list = None) -> Optional[CommandResult]:
    """
        Dumps the current iOS user interface in a serialized form.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ui = api.ios_ui_window_dump()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'ui': ui}),
            command='ios ui dump',
        )

    return output_result(
        CommandResult(result={'ui': ui}, human_text=ui),
        command='ios ui dump',
    )


def bypass_touchid(args: list = None) -> Optional[CommandResult]:
    """
        Starts a new objection job that hooks into the iOS TouchID
        classes, replacing the verification logic to always pass.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_ui_biometrics_bypass()

    return output_result(
        CommandResult(
            result={'action': 'bypass_touchid'},
            human_text='TouchID bypass started',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='ios ui bypass_touchid',
    )


def android_screenshot(args: list = None) -> Optional[CommandResult]:
    """
        Take an Android screenshot.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(status='error', result={'error': 'missing local png destination'},
                          human_text='Usage: android ui screenshot <local png destination>'),
            command='android ui screenshot',
        )

    # add the .png extension if it does not already exist
    destination = args[0] if args[0].endswith('.png') else args[0] + '.png'

    # download the file
    api = state_connection.get_api()
    data = api.android_ui_screenshot()

    image = bytearray(map(lambda x: x % 256, data))

    with open(destination, 'wb') as f:
        f.write(image)

    return output_result(
        CommandResult(result={'saved_to': destination, 'bytes': len(image)},
                      human_text='Screenshot saved to: {0}'.format(destination)),
        command='android ui screenshot',
    )


def android_flag_secure(args: list = None) -> Optional[CommandResult]:
    """
        Control FLAG_SECURE of the current Activity, allowing or disallowing
        the use of hardware key combinations and screencap to take screenshots.

        :param args:
        :return:
    """

    if len(args) <= 0 or args[0] not in ('true', 'false'):
        return output_result(
            CommandResult(status='error', result={'error': 'flag must be true or false'},
                          human_text='Usage: android ui FLAG_SECURE <true/false>'),
            command='android ui flag_secure',
        )

    api = state_connection.get_api()
    api.android_ui_set_flag_secure(args[0])

    return output_result(
        CommandResult(result={'action': 'set_flag_secure', 'value': args[0]},
                      human_text='FLAG_SECURE set to {0}'.format(args[0])),
        command='android ui flag_secure',
    )
