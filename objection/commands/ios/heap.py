import pprint

from prompt_toolkit import prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.javascript import JavascriptLexer
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def _should_ignore_methods_with_arguments(args) -> bool:
    """
        Check if the --without-arguments flag exists

        :param args:
        :return:
    """

    return len(args) > 0 and '--without-arguments' in args


def _should_print_as_utf8(args) -> bool:
    """
        Check if the --to-utf8 flag exists

        :param args:
        :return:
    """

    return len(args) > 0 and '--to-utf8' in args


def _should_return_as_string(args) -> bool:
    """
        Check if the --return-string flag exists

        :param args:
        :return:
    """

    return len(args) > 0 and '--return-string' in args


def _should_interpret_inline_js(args) -> bool:
    """
        Check if we have the --inline flag

        :param args:
        :return:
    """

    return len(args) > 0 and '--inline' in args


def instances(args: list) -> CommandResult:
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
                human_text='Usage: ios heap search instances <class> (eg: com.example.test)',
                exit_code=1,
            ),
            command='ios heap search instances',
        )

    target_class = args[0]

    api = state_connection.get_api()
    instance_results = api.ios_heap_print_live_instances(target_class)

    if len(instance_results) <= 0:
        return output_result(
            CommandResult(result={'class': target_class, 'instances': [], 'count': 0},
                          human_text='No instances found'),
            command='ios heap search instances',
        )

    human_lines = tabulate(
        [[
            entry['handle'],
            entry['kind'],
            entry['className'],
            entry.get('superClass'),
            len(entry.get('ivars', [])),
            len(entry.get('methods', [])),
        ] for entry in instance_results], headers=['Handle', 'Kind', 'Class', 'Super', 'iVars', 'Methods'],
    )
    return output_result(
        CommandResult(result={'class': target_class, 'instances': instance_results, 'count': len(instance_results)},
                      human_text=human_lines),
        command='ios heap search instances',
    )


def ivars(args: list) -> CommandResult:
    """
        Get ivars for an Objective-C object at a pointer

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing pointer'},
                status='error',
                human_text='Usage: ios heap print ivars <pointer> (eg: 0x600001130660)',
                exit_code=1,
            ),
            command='ios heap print ivars',
        )

    target_pointer = args[0]

    api = state_connection.get_api()
    ivar_results = api.ios_heap_print_ivars(target_pointer, _should_print_as_utf8(args))

    human_lines = tabulate(
        [[key, value] for key, value in ivar_results[1].items()], headers=['iVar', 'Value'],
    )
    return output_result(
        CommandResult(
            result={'pointer': target_pointer, 'class': ivar_results[0], 'ivars': ivar_results[1],
                    'to_utf8': _should_print_as_utf8(args)},
            human_text=human_lines,
        ),
        command='ios heap print ivars',
    )


def methods(args: list) -> CommandResult:
    """
        Get methods for an Objective-C object at a pointer

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing pointer'},
                status='error',
                human_text='Usage: ios heap print methods <pointer> (eg: 0x600001130660)',
                exit_code=1,
            ),
            command='ios heap print methods',
        )

    target_pointer = args[0]

    api = state_connection.get_api()
    method_results = api.ios_heap_print_methods(target_pointer)

    if _should_ignore_methods_with_arguments(args):
        method_results[1] = list(filter(lambda x: ':' not in x, method_results[1]))

    human_lines = tabulate(
        [[
            entry,
            entry.split(' ')[0],
            '{type} [{clazz} {method}]'.format(
                type=entry.split(' ')[0], clazz=method_results[0], method=entry.split(' ')[1])
        ] for entry in method_results[1]], headers=['Method', 'Type', 'Full'],
    )
    return output_result(
        CommandResult(
            result={'pointer': target_pointer, 'class': method_results[0], 'methods': method_results[1],
                    'count': len(method_results[1])},
            human_text=human_lines,
        ),
        command='ios heap print methods',
    )


def execute(args: list) -> CommandResult:
    """
        Executes a method on a pointer which is assumed to be an Objective-C
        object.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing arguments'},
                status='error',
                human_text='Usage: ios heap execute method <pointer> <method> (eg: 0x600001130660)',
                exit_code=1,
            ),
            command='ios heap execute method',
        )

    target_pointer = args[0]
    method = args[1]

    if ':' in method:
        return output_result(
            CommandResult(
                result={'error': 'only methods that do not require arguments are supported'},
                status='error',
                human_text='Unfortunately, only methods that do not require arguments are supported.',
                exit_code=1,
            ),
            command='ios heap execute method',
        )

    api = state_connection.get_api()
    exec_results = api.ios_heap_exec_method(target_pointer, method, _should_return_as_string(args))

    human_text = pprint.pformat(exec_results)
    return output_result(
        CommandResult(
            result={'pointer': target_pointer, 'method': method, 'result': exec_results,
                    'as_string': _should_return_as_string(args)},
            human_text=human_text,
        ),
        command='ios heap execute method',
    )


def evaluate(args: list) -> CommandResult:
    """
        Evaluate JavaScript on an Objective-C pointer.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing pointer'},
                status='error',
                human_text='Usage: ios heap execute js <pointer> [--inline <js>]',
                exit_code=1,
            ),
            command='ios heap execute js',
        )

    target_pointer = args[0]

    if _should_interpret_inline_js(args):
        args = list(args)
        args.remove('--inline')
        js = ' '.join(args[1:])
    else:
        js = prompt(
            multiline=True, lexer=PygmentsLexer(JavascriptLexer),
            bottom_toolbar='JavaScript edit mode. [ESC] and then [ENTER] to accept. [CTRL] + C to cancel.').strip()

        return output_result(
            CommandResult(
                result={'action': 'evaluated_js', 'pointer': target_pointer},
                human_text='JavaScript capture complete. Evaluating...',
                warnings=['JS evaluation results, if any, are emitted by the agent as async messages.'],
            ),
            command='ios heap execute js',
        )

    api = state_connection.get_api()
    api.ios_heap_evaluate_js(target_pointer, js)

    return output_result(
        CommandResult(
            result={'action': 'evaluated_js', 'pointer': target_pointer},
            human_text='JavaScript capture complete. Evaluating...',
            warnings=['JS evaluation results, if any, are emitted by the agent as async messages.'],
        ),
        command='ios heap execute js',
    )