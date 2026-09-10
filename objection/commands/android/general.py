from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def deoptimise(args: list) -> Optional[CommandResult]:
    """
        Forces the VM to execute everything with its interpreter.
        Necessary to prevent optimizations from bypassing method hooks in some cases.

        Ref: https://frida.re/docs/javascript-api/

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_deoptimize()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'action': 'deoptimize'}),
            command='android deoptimize',
        )
    return None
