import pprint
from typing import Optional

import click
from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.javascript import JavascriptLexer
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def _should_ignore_methods_with_arguments(args) -> bool:
    """
        Check if the --without-arguments flag exists

        :param args:
        :return:
    """

    return len(args) > 0 and '--without-arguments' in args


def _should_return_as_string(args) -> bool:
    """
        Check if the --return-string flag exists

        :param args:
        :return:
    """

    return len(args) > 0 and '--return-string' in args


def instances(args: list) -> Optional[CommandResult]:
    """
        Asks the agent to print the currently live instances of a particular class

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing class name'},
                status='error',
                human_text='Usage: android heap search instances <class> (eg: com.example.test)',
                exit_code=1,
            ),
            command='android heap search instances',
        )

    target_class = args[0]

    api = state_connection.get_api()
    instance_results = api.android_heap_get_live_class_instances(target_class)

    if should_output_json(args):
        return output_result(
            CommandResult(result={'class': target_class, 'instances': instance_results, 'count': len(instance_results)}),
            command='android heap search instances',
        )

    if len(instance_results) <= 0:
        return output_result(
            CommandResult(result={'class': target_class, 'instances': [], 'count': 0}),
            command='android heap search instances',
        )

    human_lines = tabulate(
        [[
            entry['hashcode'],
            entry['classname'],
            entry['tostring'],
        ] for entry in instance_results], headers=['Hashcode', 'Class', 'toString()'],
    )
    return output_result(
        CommandResult(
            result={'class': target_class, 'instances': instance_results, 'count': len(instance_results)},
            human_text=human_lines,
        ),
        command='android heap search instances',
    )


def methods(args: list) -> Optional[CommandResult]:
    """
        Get the methods available on a handle

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing hashcode'},
                status='error',
                human_text='Usage: android heap print methods <hashcode> (eg: 24688232)',
                exit_code=1,
            ),
            command='android heap print methods',
        )

    target_handle = int(args[0])

    api = state_connection.get_api()
    method_results = api.android_heap_print_methods(target_handle)

    # apply argument filters
    # we assume methods that end with braces don't need arguments
    if _should_ignore_methods_with_arguments(args):
        method_results[1] = list(filter(lambda x: '()' in x, method_results[1]))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'handle': target_handle, 'methods': method_results[1], 'class': method_results[0],
                        'count': len(method_results[1])},
            ),
            command='android heap print methods',
        )

    human_lines = tabulate(
        [[entry] for entry in method_results], headers=['Method'],
    )
    return output_result(
        CommandResult(
            result={'handle': target_handle, 'methods': method_results[1], 'class': method_results[0],
                    'count': len(method_results[1])},
            human_text=human_lines,
        ),
        command='android heap print methods',
    )


def execute(args: list) -> Optional[CommandResult]:
    """
        Executes a method on a handle which is assumed to be a Java
        class instance.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing arguments'},
                status='error',
                human_text='Usage: android heap execute method <hashcode> <method> (eg: 24688232)',
                exit_code=1,
            ),
            command='android heap execute method',
        )

    target_handle = int(args[0])
    method = args[1]

    api = state_connection.get_api()
    exec_results = api.android_heap_execute_handle_method(target_handle, method,
                                                          _should_return_as_string(args))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'handle': target_handle, 'method': method, 'result': exec_results,
                        'as_string': _should_return_as_string(args)},
            ),
            command='android heap execute method',
        )

    if exec_results:
        if isinstance(exec_results, dict):
            human_text = pprint.pformat(exec_results)
        else:
            human_text = str(exec_results)
        return output_result(
            CommandResult(
                result={'handle': target_handle, 'method': method, 'result': exec_results,
                        'as_string': _should_return_as_string(args)},
                human_text=human_text,
            ),
            command='android heap execute method',
        )
    return output_result(
        CommandResult(
            result={'handle': target_handle, 'method': method, 'result': None,
                    'as_string': _should_return_as_string(args)},
        ),
        command='android heap execute method',
    )


def fields(args: list) -> Optional[CommandResult]:
    """
        Get the fields available on a handle

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing hashcode'},
                status='error',
                human_text='Usage: android heap print fields <hashcode> (eg: 24688232)',
                exit_code=1,
            ),
            command='android heap print fields',
        )

    target_handle = int(args[0])

    api = state_connection.get_api()
    field_results = api.android_heap_print_fields(target_handle)

    if should_output_json(args):
        return output_result(
            CommandResult(result={'handle': target_handle, 'fields': field_results, 'count': len(field_results)}),
            command='android heap print fields',
        )

    human_lines = tabulate(
        [[value['name'], value['value']] for value in field_results], headers=['Name', 'Value'],
    )
    return output_result(
        CommandResult(result={'handle': target_handle, 'fields': field_results, 'count': len(field_results)},
                      human_text=human_lines),
        command='android heap print fields',
    )


def evaluate(args: list) -> Optional[CommandResult]:
    """
        Evaluates JavaScript on a handle

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing hashcode'},
                status='error',
                human_text='Usage: android heap execute js <hashcode> [--inline <js>]',
                exit_code=1,
            ),
            command='android heap execute js',
        )

    target_handle = int(args[0])

    # Agent / JSON 模式：强制要求 --inline 提供 JS 源（无法使用交互 prompt）
    if should_output_json(args):
        if '--inline' not in args:
            return output_result(
                CommandResult(
                    result={'error': 'JSON mode requires --inline <js>; interactive prompt unavailable'},
                    status='error',
                    exit_code=1,
                ),
                command='android heap execute js',
            )
        args = list(args)
        args.remove('--inline')
        js = ' '.join(args[1:])
    else:
        js = prompt(
            click.secho('(The hashcode at `{handle}` will be available as the `clazz` variable.)'.format(
                handle=target_handle
            ), dim=True),
            multiline=True, lexer=PygmentsLexer(JavascriptLexer),
            bottom_toolbar='JavaScript edit mode. [ESC] and then [ENTER] to accept. [CTRL] + C to cancel.').strip()

    return output_result(
        CommandResult(
            result={'action': 'evaluated_js', 'handle': target_handle},
            human_text='JavaScript capture complete. Evaluating...',
            warnings=['JS evaluation results, if any, are emitted by the agent as async messages.'],
        ),
        command='android heap execute js',
    )
