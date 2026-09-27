
from objection.state.connection import state_connection
from objection.utils.helpers import clean_argument_flags
from objection.utils.output import CommandResult, output_result


def _should_dump_backtrace(args: list = None) -> bool:
    """
        Check if --dump-backtrace is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-backtrace' in args


def analyze_implicit_intents(args: list) -> CommandResult:
    """
        Analyzes implicit intents in hooked methods.
    """
    api = state_connection.get_api()
    should_backtrace = _should_dump_backtrace(args)

    api.android_intent_analyze(should_backtrace)
    return output_result(
        CommandResult(
            result={'action': 'analyze_implicit_intents', 'dump_backtrace': should_backtrace},
            human_text='Started implicit intent analysis with backtrace' if should_backtrace else 'Started implicit intent analysis',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                      'Intent activity-service broadcasts arrive as async messages; poll via `agent state` or HTTP /events.'],
        ),
        command='android intent analyze_implicit_intents',
    )


def launch_activity(args: list) -> CommandResult:
    """
        Launches an activity class using an Android Intent

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 1:
        return output_result(
            CommandResult(
                status='error',
                result={'error': 'missing activity_class'},
                human_text='Usage: android intent launch_activity <activity_class>',
                exit_code=1,
            ),
            command='android intent launch_activity',
        )

    intent_class = args[0]

    api = state_connection.get_api()
    api.android_intent_start_activity(intent_class)

    return output_result(
        CommandResult(result={'action': 'launch_activity', 'activity': intent_class}),
        command='android intent launch_activity',
    )


def launch_service(args: list) -> CommandResult:
    """
        Launches an exported service using an Android Intent

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 1:
        return output_result(
            CommandResult(
                status='error',
                result={'error': 'missing service_class'},
                human_text='Usage: android intent launch_service <service_class>',
                exit_code=1,
            ),
            command='android intent launch_service',
        )

    intent_class = args[0]

    api = state_connection.get_api()
    api.android_intent_start_service(intent_class)

    return output_result(
        CommandResult(result={'action': 'launch_service', 'service': intent_class}),
        command='android intent launch_service',
    )
