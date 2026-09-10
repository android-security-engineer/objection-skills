import os
from typing import Optional

import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json
from ..utils.helpers import sizeof_fmt, clean_argument_flags


def _should_disable_exception_handler(args: list = None) -> bool:
    """
        Checks the arguments if '--no-exception-handler'
        is part of it.

        :param args:
        :return:
    """

    return len(args) > 0 and '--no-exception-handler' in args


def frida_environment(args: list = None) -> Optional[CommandResult]:
    """
        Prints information about the current Frida environment.

        :param args:
        :return:
    """

    frida_env = state_connection.get_api().env_frida()

    if should_output_json(args):
        return output_result(
            CommandResult(result=frida_env),
            command='frida_environment',
        )

    click.secho(tabulate([
        ('Frida Version', frida_env['version']),
        ('Process Architecture', frida_env['arch']),
        ('Process Platform', frida_env['platform']),
        ('Debugger Attached', frida_env['debugger']),
        ('Script Runtime', frida_env['runtime']),
        ('Frida Heap Size', sizeof_fmt(frida_env['heap']))
    ]))
    return None


def ping(args: list = None) -> Optional[CommandResult]:
    """
        Pings the agent.

        :param args:
        :return:
    """

    agent = state_connection.get_api()
    ok = agent.ping()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'ok': bool(ok)}, status='ok' if ok else 'error', exit_code=0 if ok else 1),
            command='ping',
        )

    if ok:
        click.secho('The agent responds ok!', fg='green')
    else:
        click.secho('The agent did not respond ok!', fg='red')
    return None


def load_background(args: list = None) -> Optional[CommandResult]:
    """
        Loads a Frida script and runs it in the background.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing script path'},
                    status='error',
                    human_text='Usage: import <local path to frida-script> (optional name)',
                    exit_code=1,
                ),
                command='import',
            )
        click.secho('Usage: import <local path to frida-script> (optional name)',
                    bold=True)
        return None

    source = args[0]

    # support ~ syntax
    if source.startswith('~'):
        source = os.path.expanduser(source)

    if not os.path.isfile(source):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'file not found', 'path': source},
                    status='error',
                    exit_code=1,
                ),
                command='import',
            )
        click.secho('Unable to import file {0}'.format(source), fg='red')
        return None

    # read the hook sources
    with open(source, 'r') as f:
        hook = ''.join(f.read())

    agent = state_connection.get_agent()
    agent.attach_script(source, hook)

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'imported', 'source': source},
                warnings=['Background script output arrives as async messages; poll via `agent state` or HTTP /events.'],
            ),
            command='import',
        )
    return None

