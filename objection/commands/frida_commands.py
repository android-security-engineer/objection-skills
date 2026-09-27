import os


from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result
from ..utils.helpers import sizeof_fmt, clean_argument_flags


def _should_disable_exception_handler(args: list = None) -> bool:
    """
        Checks the arguments if '--no-exception-handler'
        is part of it.

        :param args:
        :return:
    """

    return len(args) > 0 and '--no-exception-handler' in args


def frida_environment(args: list = None) -> CommandResult:
    """
        Prints information about the current Frida environment.

        :param args:
        :return:
    """

    frida_env = state_connection.get_api().env_frida()

    human_text = tabulate([
        ('Frida Version', frida_env['version']),
        ('Process Architecture', frida_env['arch']),
        ('Process Platform', frida_env['platform']),
        ('Debugger Attached', frida_env['debugger']),
        ('Script Runtime', frida_env['runtime']),
        ('Frida Heap Size', sizeof_fmt(frida_env['heap']))
    ])
    return output_result(
        CommandResult(result=frida_env, human_text=human_text),
        command='frida_environment',
    )


def ping(args: list = None) -> CommandResult:
    """
        Pings the agent.

        :param args:
        :return:
    """

    agent = state_connection.get_api()
    ok = agent.ping()

    human_text = 'The agent responds ok!' if ok else 'The agent did not respond ok!'
    return output_result(
        CommandResult(result={'ok': bool(ok)}, status='ok' if ok else 'error', human_text=human_text),
        command='ping',
    )


def load_background(args: list = None) -> CommandResult:
    """
        Loads a Frida script and runs it in the background.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing script path'},
                status='error',
                human_text='Usage: import <local path to frida-script> (optional name)',
                exit_code=1,
            ),
            command='import',
        )

    source = args[0]

    # support ~ syntax
    if source.startswith('~'):
        source = os.path.expanduser(source)

    if not os.path.isfile(source):
        return output_result(
            CommandResult(
                result={'error': 'file not found', 'path': source},
                status='error',
                human_text='Unable to import file {0}'.format(source),
                exit_code=1,
            ),
            command='import',
        )

    # read the hook sources
    with open(source, 'r') as f:
        hook = ''.join(f.read())

    agent = state_connection.get_agent()
    agent.attach_script(source, hook)

    return output_result(
        CommandResult(
            result={'action': 'imported', 'source': source},
            human_text='Background script loaded: {0}'.format(source),
            warnings=['Background script output arrives as async messages; poll via `agent state` or HTTP /events.'],
        ),
        command='import',
    )

