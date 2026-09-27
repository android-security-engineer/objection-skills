import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def get(args: list = None) -> CommandResult:
    """
        Gets all of the values stored in NSUserDefaults and prints
        them to screen.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    defaults = api.ios_nsuser_defaults_get()

    return output_result(
        CommandResult(result=defaults, human_text=str(defaults)),
        command='ios nsuserdefaults get',
    )
