from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def crypto_enable(args: list = None) -> CommandResult:
    """
        Attempts to enable ios crypto monitoring.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_monitor_crypto_enable()

    return output_result(
        CommandResult(
            result={'action': 'crypto_monitoring_enabled'},
            human_text='iOS crypto monitoring enabled',
            warnings=['Crypto events arrive as async messages; poll via `agent state` or HTTP /events.',
                      'Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='ios monitor crypto',
    )
