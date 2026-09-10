from typing import Optional

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def _should_be_quiet(args: list) -> bool:
    """
        Checks if --quiet is part of the
        commands arguments.

        :param args:
        :return:
    """

    return '--quiet' in args


def ios_disable(args: list = None) -> Optional[CommandResult]:
    """
        Starts a new objection job that hooks common classes and functions,
        applying new logic in an attempt to bypass SSL pinning.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_pinning_disable(_should_be_quiet(args))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'ssl_pinning_disabled', 'quiet': _should_be_quiet(args)},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios sslpinning disable',
        )
    return None
