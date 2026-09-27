
from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def execute(args: list) -> CommandResult:
    """
        Runs a shell command on an Android device.

        :param args:
        :return:
    """

    command = ' '.join(args)
    human_text = 'Running shell command: {0}\n'.format(command)

    api = state_connection.get_api()
    response = api.android_shell_exec(command)

    stdout = response.get('stdOut', '') if isinstance(response, dict) else ''
    stderr = response.get('stdErr', '') if isinstance(response, dict) else ''

    human_text += stdout
    if stderr:
        human_text += stderr

    return output_result(
        CommandResult(result={'command': command, 'stdout': stdout, 'stderr': stderr},
                      human_text=human_text),
        command='android shell_exec',
    )
