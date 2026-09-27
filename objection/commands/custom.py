import os

import frida

from objection.utils.output import CommandResult, output_result
from typing import Optional

import frida

from objection.utils.output import CommandResult, output_result
from ..state.connection import state_connection


def evaluate(args: list) -> CommandResult:
    """
        Evaluate JavaScript within the agent's context.

        :param args:
        :return:
    """

    if len(args) <= 0:
        human_text = 'Usage: evaluate <local path to js file>'
        return output_result(
            CommandResult(
                result={'error': 'JSON mode requires a file path argument (interactive prompt unavailable)'},
                status='error',
                human_text=human_text,
                exit_code=1,
            ),
            command='evaluate',
        )

    target_file = args[0]
    p = os.path.expanduser(target_file)
    if os.path.exists(p):
        target_file = p
    else:
        human_text = 'Could not find file {p}.'.format(p=target_file)
        return output_result(
            CommandResult(
                result={'error': 'file not found', 'path': target_file},
                status='error',
                human_text=human_text,
                exit_code=1,
            ),
            command='evaluate',
        )

    with open(target_file, 'r', encoding='utf-8') as f:
        javascript = ''.join(f.readlines())

    if len(javascript) <= 0:
        human_text = 'JavaScript to evaluate appears empty. Skipping.'
        return output_result(
            CommandResult(
                result={'error': 'javascript appears empty'},
                status='error',
                human_text=human_text,
                exit_code=1,
            ),
            command='evaluate',
        )

    human_text = 'JavaScript capture complete. Evaluating...'
    try:
        state_connection.get_api().evaluate(javascript)
    except frida.core.RPCException as e:
        human_text = 'Failed to load script: {}'.format(e)
        return output_result(
            CommandResult(
                result={'error': 'failed to load script', 'detail': str(e)},
                status='error',
                human_text=human_text,
                exit_code=1,
            ),
            command='evaluate',
        )

    return output_result(
        CommandResult(
            result={'action': 'evaluated', 'source': target_file},
            human_text=human_text,
            warnings=['Evaluation output, if any, is emitted by the agent as async messages.'],
        ),
        command='evaluate',
    )
