from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def disable(args: list = None) -> None:
    """
        Performs a generic anti root detection.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_root_detection_disable()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'root_detection_disabled'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android root disable',
        )
    return None


def simulate(args: list = None) -> None:
    """
        Simulate a rooted environment.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_root_detection_enable()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'root_detection_simulated'},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android root simulate',
        )
    return None
