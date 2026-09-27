from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def disable(args: list = None) -> CommandResult:
    """
        Attempts to disable jailbreak detection.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_jailbreak_disable()

    return output_result(
        CommandResult(
            result={'action': 'jailbreak_detection_disabled'},
            human_text='Jailbreak detection disabled',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='ios jailbreak disable',
    )


def simulate(args: list = None) -> CommandResult:
    """
        Attempts to simulate a Jailbroken environment

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_jailbreak_enable()

    return output_result(
        CommandResult(
            result={'action': 'jailbreak_simulated'},
            human_text='Jailbreak simulated',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='ios jailbreak simulate',
    )
