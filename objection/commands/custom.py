import os
from typing import Optional

import click
import frida
from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.javascript import JavascriptLexer

from objection.utils.output import CommandResult, output_result, should_output_json
from ..state.connection import state_connection


def evaluate(args: list) -> Optional[CommandResult]:
    """
        Evaluate JavaScript within the agent's context.

        :param args:
        :return:
    """

    target_file = None

    # Agent / JSON 模式：必须提供文件路径，交互 prompt 不可用
    if should_output_json(args):
        if len(args) <= 0:
            return output_result(
                CommandResult(
                    result={'error': 'JSON mode requires a file path argument (interactive prompt unavailable)'},
                    status='error',
                    human_text='Usage: evaluate <local path to js file>',
                    exit_code=1,
                ),
                command='evaluate',
            )
        target_file = os.path.expanduser(args[0])
        if not os.path.exists(target_file):
            return output_result(
                CommandResult(
                    result={'error': 'file not found', 'path': target_file},
                    status='error',
                    exit_code=1,
                ),
                command='evaluate',
            )
        with open(target_file, 'r', encoding='utf-8') as f:
            javascript = ''.join(f.readlines())
    else:
        # if we have an argument, let's assume it is a file path
        if len(args) > 0:

            target_file = args[0]
            p = os.path.expanduser(target_file)
            if os.path.exists(p):
                target_file = p
            else:
                click.secho('Could not find file {p}.'.format(p=target_file), fg='red')
                return None

        if target_file:
            with open(target_file, 'r', encoding='utf-8') as f:
                javascript = ''.join(f.readlines())
        else:
            javascript = prompt(
                multiline=True, lexer=PygmentsLexer(JavascriptLexer),
                bottom_toolbar='JavaScript edit mode. [ESC] and then [ENTER] to accept. [CTRL] + C to cancel.').strip()

    if len(javascript) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'javascript appears empty'},
                    status='error',
                    exit_code=1,
                ),
                command='evaluate',
            )
        click.secho('JavaScript to evaluate appears empty. Skipping.', fg='yellow')
        return None

    click.secho('JavaScript capture complete. Evaluating...', dim=True)
    try:
        state_connection.get_api().evaluate(javascript)
    except frida.core.RPCException as e:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'failed to load script', 'detail': str(e)},
                    status='error',
                    exit_code=1,
                ),
                command='evaluate',
            )
        click.secho('Failed to load script: {}'.format(e), fg='red', bold=True)
        return None

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'evaluated', 'source': target_file},
                warnings=['Evaluation output, if any, is emitted by the agent as async messages.'],
            ),
            command='evaluate',
        )
    return None
