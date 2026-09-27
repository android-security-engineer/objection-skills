
from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def deoptimise(args: list) -> CommandResult:
    """
        Forces the VM to execute everything with its interpreter.
        Necessary to prevent optimizations from bypassing method hooks in some cases.

        Ref: https://frida.re/docs/javascript-api/

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_deoptimize()

    return output_result(
        CommandResult(result={'action': 'deoptimize'}, human_text='Android deoptimized'),
        command='android deoptimize',
    )
