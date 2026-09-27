from ..commands.filemanager import pwd
from ..state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def start(args: list) -> CommandResult:
    """
        Start's an http server, exposing the mobile devices filesystem.

        :param args:
        :return:
    """

    port = 9000

    if len(args) > 0:
        port = int(args[0])

    api = state_connection.get_api()
    api.http_server_start(pwd(), port)

    return output_result(
        CommandResult(result={'action': 'http_start', 'port': port, 'root': pwd()},
                      human_text='Starting server on port {port}...'.format(port=port)),
        command='http start',
    )


def stop(args: list) -> CommandResult:
    """
        Stops the on device HTTP server

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.http_server_stop()

    return output_result(
        CommandResult(result={'action': 'http_stop'}, human_text='HTTP server stopped'),
        command='http stop',
    )


def status(args: list) -> CommandResult:
    """
        Get the status of the HTTP server

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.http_server_status()

    return output_result(
        CommandResult(result={'action': 'http_status'}, human_text='HTTP server status retrieved'),
        command='http status',
    )
