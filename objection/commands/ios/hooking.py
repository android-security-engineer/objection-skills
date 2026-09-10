import json
from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.helpers import clean_argument_flags
from objection.utils.output import CommandResult, output_result, should_output_json

# a thumb sucked list of prefixes used in Objective-C runtime
# for iOS applications. This is not a science, but a gut feeling.
native_prefixes = [
    '_',
    'NS',
    # '_NS',
    # '__NS',
    'CF',
    'OS_',
    'UI',
    # '_UI',

    'AWD',
    'GEO',

    'AC',
    'AF',
    'AU',
    'AV',
    'BK',
    'BS',
    'CA',
    'CB',
    'CI',
    'CL',
    'CT',
    'CUI',
    'DOM',
    'FBS',
    'LA',
    'LS',
    'MC',
    'MTL',
    'PFUbiquity',
    'PKPhysics',
    'SBS',
    'TI',
    'TXR',
    'UM',
    'Web',
]


def _should_ignore_native_classes(args: list) -> bool:
    """
        Checks if --ignore-native is in a list of tokens received
        from the commandline.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return False

    return '--ignore-native' in args


def _should_include_parent_methods(args: list) -> bool:
    """
        Checks if --include-parents exists in a list of tokens received
        from the commandline.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return False

    return '--include-parents' in args


def _class_is_prefixed_with_native(class_name: str) -> bool:
    """
        Check if a class name received is prefixed with one of the
        prefixes in the native_prefixes list.

        :param class_name:
        :return:
    """

    for prefix in native_prefixes:

        if class_name.startswith(prefix):
            return True

    return False


def _string_is_true(s: str) -> bool:
    """
        Check if a string should be considered as "True"

        :param s:
        :return:
    """

    return s.lower() in ('true', 'yes')


def _should_dump_backtrace(args: list) -> bool:
    """
        Check if --dump-backtrace is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-backtrace' in args


def _should_dump_args(args: list) -> bool:
    """
        Check if --dump-args is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-args' in args


def _should_dump_return_value(args: list) -> bool:
    """
        Check if --dump-return is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-return' in args


def _should_print_only_classes(args: list) -> bool:
    """
        Check if --only-classes is part of the arguments.

        :param args:
        :return:
    """

    return '--only-classes' in args


def _should_dump_json(args: list) -> bool:
    """
        Check if --json is part of the arguments.

        :param args:
        :return:
    """

    return '--json' in args


def _should_be_quiet(args: list) -> bool:
    """
        Check if --quiet is part of the arguments.

        :param args:
        :return:
    """

    return '--quiet' in args


def _get_flag_value(flag: str, args: list) -> Optional[str]:
    """
        Gets the value for a flag

        :param flag:
        :param args:
        :return:
    """

    target = None

    for i in range(len(args)):
        if args[i] == flag:
            target = i + 1

    if target is None:
        return None
    elif target < len(args):
        return args[target]
    else:
        return None


def show_ios_classes(args: list = None) -> Optional[CommandResult]:
    """
        Prints the classes available in the current Objective-C
        runtime to the screen.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    classes = api.ios_hooking_get_classes()

    if should_output_json(args):
        if _should_ignore_native_classes(args):
            classes = sorted([c for c in classes if not _class_is_prefixed_with_native(c)])
        else:
            classes = sorted(classes)
        return output_result(
            CommandResult(
                result={'classes': classes, 'count': len(classes), 'ignored_native': _should_ignore_native_classes(args)},
            ),
            command='ios hooking list classes',
        )

    # loop the class names and check if we should be ignoring it.
    for class_name in sorted(classes):
        if _should_ignore_native_classes(args):
            if not _class_is_prefixed_with_native(class_name):
                click.secho(class_name)
                continue

        else:
            click.secho(class_name)

    click.secho('\nFound {0} classes'.format(len(classes)), bold=True)
    return None


def show_ios_class_methods(args: list) -> Optional[CommandResult]:
    """
        Displays the methods available in a class.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing class name'},
                    status='error',
                    human_text='Usage: ios hooking list class_methods <class name> (--include-parents)',
                    exit_code=1,
                ),
                command='ios hooking list class_methods',
            )
        click.secho('Usage: ios hooking list class_methods <class name> (--include-parents)', bold=True)
        return None

    classname = args[0]

    api = state_connection.get_api()
    methods = api.ios_hooking_get_class_methods(classname, _should_include_parent_methods(args))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'class': classname, 'methods': methods, 'count': len(methods),
                        'include_parents': _should_include_parent_methods(args)},
            ),
            command='ios hooking list class_methods',
        )

    if len(methods) > 0:

        # dump the methods to screen
        for method in methods:
            click.secho(method)

        click.secho('\nFound {0} methods'.format(len(methods)), bold=True)

    else:
        click.secho('No class / methods found')
    return None


def set_method_return_value(args: list) -> Optional[CommandResult]:
    """
        Make an Objective-C method return a specific boolean
        value, always.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 2:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing arguments'},
                    status='error',
                    human_text='Usage: ios hooking set_method_return "<selector>" (eg: "-[ClassName methodName:]") <true/false>',
                    exit_code=1,
                ),
                command='ios hooking set_method_return',
            )
        click.secho('Usage: ios hooking set_method_return "<selector>" (eg: "-[ClassName methodName:]") <true/false>',
                    bold=True)
        return None

    selector = args[0]
    retval = args[1]

    api = state_connection.get_api()
    api.ios_hooking_set_return_value(selector, _string_is_true(retval))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'action': 'set_return_value', 'selector': selector, 'value': _string_is_true(retval)},
                warnings=['Hook installed; existing invocations are affected immediately.',
                          'Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='ios hooking set_method_return',
        )
    return None


def watch(args: list) -> Optional[CommandResult]:
    """
        Watches a pattern for invocations.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing pattern'},
                    status='error',
                    human_text='Usage: ios hooking watch <pattern>',
                    exit_code=1,
                ),
                command='ios hooking watch',
            )
        click.secho('Usage: ios hooking watch <pattern>', bold=True)
        return None

    pattern = args[0]

    api = state_connection.get_api()
    api.ios_hooking_watch(pattern,
                          _should_dump_args(args),
                          _should_dump_backtrace(args),
                          _should_dump_return_value(args),
                          _should_include_parent_methods(args))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={
                    'action': 'watching',
                    'pattern': pattern,
                    'dump_args': _should_dump_args(args),
                    'dump_backtrace': _should_dump_backtrace(args),
                    'dump_return': _should_dump_return_value(args),
                    'include_parents': _should_include_parent_methods(args),
                },
                warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                          'Hook invocations arrive as async messages; poll via `agent state` or HTTP /events.'],
            ),
            command='ios hooking watch',
        )
    return None


def search(args: list) -> Optional[CommandResult]:
    """
        Searches the current iOS application for classes and methods.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing pattern'},
                    status='error',
                    human_text="Usage: ios hooking search '<pattern/string>'",
                    exit_code=1,
                ),
                command='ios hooking search',
            )
        click.secho('Usage: ios hooking search \'<pattern/string>\'', bold=True)
        return None

    api = state_connection.get_api()
    pattern = args[0]

    results = api.ios_hooking_search(pattern)
    data = {}

    # build a list of results to print / dump later
    for func in results:
        fullname = func['name']
        start_bracket = fullname.find('[') + 1
        class_name = fullname[start_bracket: fullname.find(' ')]
        if data.get(class_name) is not None:
            data[class_name].append(fullname)
        else:
            data[class_name] = [fullname]

    if should_output_json(args):
        target_file = _get_flag_value('--json', args)
        # --json <filename> 保留旧行为：写文件
        if target_file:
            with open(target_file, 'w') as fd:
                fd.write(json.dumps({
                    'meta': {
                        'runtime': 'objc'
                    },
                    'classes': data
                }))
            return output_result(
                CommandResult(result={'dumped_to': target_file, 'class_count': len(data)}),
                command='ios hooking search',
            )

        # 全局 JSON 模式（agent exec）：走统一输出层到 stdout
        return output_result(
            CommandResult(result={'runtime': 'objc', 'classes': data, 'class_count': len(data)}),
            command='ios hooking search',
        )

    # Print the matching methods
    for klass in data.keys():
        if _should_print_only_classes(args):
            print(klass)
            continue

        methods = data[klass]
        for method in methods:
            print(f'{method}')

    return None
