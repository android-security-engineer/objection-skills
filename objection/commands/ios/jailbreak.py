from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def disable(args: list = None) -> Optional[CommandResult]:
    """
        Attempts to disable jailbreak detection.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_jailbreak_disable()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'jailbreak_detection_disabled'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios jailbreak disable',
        )
    return None


def simulate(args: list = None) -> Optional[CommandResult]:
    """
        Attempts to simulate a Jailbroken environment

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_jailbreak_enable()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'jailbreak_simulated'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios jailbreak simulate',
        )
    return None
