import json
from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.helpers import clean_argument_flags
from objection.utils.output import CommandResult, output_result, should_output_json


def _is_pattern_or_constant(s: str) -> bool:
    """
        Check if a provided pattern matches "CLASS!METHOD"

        :param s:
        :return:
    """

    # No pattern case
    if "!" not in s:
        return True

    # Check if CLASS and METHOD is defined at all
    parts = s.split('!')
    if len(parts) != 2:
        return False
    elif len(parts[0]) == 0 or len(parts[1]) == 0:
        return False

    return True


def _string_is_true(s: str) -> bool:
    """
        Check if a string should be considered as "True"

        :param s:
        :return:
    """

    return s.lower() in ('true', 'yes')


def _should_dump_backtrace(args: list = None) -> bool:
    """
        Check if --dump-backtrace is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-backtrace' in args


def _should_watch(args: list = None) -> bool:
    """
        Check if --dump-args is part of the arguments.

        :param args:
        :return:
    """

    return '--watch' in args


def _should_dump_args(args: list = None) -> bool:
    """
        Check if --dump-args is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-args' in args


def _should_dump_return_value(args: list = None) -> bool:
    """
        Check if --dump-return is part of the arguments.

        :param args:
        :return:
    """

    return '--dump-return' in args


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


def _should_print_only_classes(args: list = None) -> bool:
    """
        Check if --only-classes is part of the arguments.

        :param args:
        :return:
    """

    return '--only-classes' in args


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


def show_android_classes(args: list = None) -> Optional[CommandResult]:
    """
        Show the currently loaded classes.
        Note that Java classes are only loaded when they are used,
        so not all classes may be present.

        :return:
    """

    api = state_connection.get_api()
    classes = sorted(api.android_hooking_get_classes())

    if should_output_json(args):
        return output_result(
            CommandResult(result={'classes': classes, 'count': len(classes)}),
            command='android hooking list classes',
        )

    # print the enumerated classes
    for class_name in classes:
        click.secho(class_name)

    click.secho('\nFound {0} classes'.format(len(classes)), bold=True)
    return None


def show_android_class_loaders(args: list = None) -> Optional[CommandResult]:
    """
        Show the currently registered class loaders.

        :return:
    """

    api = state_connection.get_api()
    loaders = sorted(api.android_hooking_get_class_loaders())

    if should_output_json(args):
        return output_result(
            CommandResult(result={'class_loaders': loaders, 'count': len(loaders)}),
            command='android hooking list class_loaders',
        )

    # print the enumerated classes
    for loader in loaders:
        click.secho('* {0}'.format(loader))

    click.secho('\nFound {0} class loaders'.format(len(loaders)), bold=True)
    return None


def show_android_class_methods(args: list = None) -> Optional[CommandResult]:
    """
        Shows the methods available on an Android class.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing class name'},
                    status='error',
                    human_text='Usage: android hooking list class_methods <class name>',
                    exit_code=1,
                ),
                command='android hooking list class_methods',
            )
        click.secho('Usage: android hooking list class_methods <class name>', bold=True)
        return None

    class_name = args[0]

    api = state_connection.get_api()
    methods = sorted(api.android_hooking_get_class_methods(class_name))

    if should_output_json(args):
        return output_result(
            CommandResult(result={'class': class_name, 'methods': methods, 'count': len(methods)}),
            command='android hooking list class_methods',
        )

    # print the enumerated classes
    for method in methods:
        click.secho(method)

    click.secho('\nFound {0} method(s)'.format(len(methods)), bold=True)
    return None


def notify(args: list = None) -> Optional[CommandResult]:
    """
        Notify when a class becomes available.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing pattern'},
                    status='error',
                    human_text='Usage: android hooking notify <pattern>',
                    exit_code=1,
                ),
                command='android hooking notify',
            )
        click.secho('Usage: android hooking notify <pattern>', bold=True)
        return None

    query = args[0]
    if not _is_pattern_or_constant(query):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'incorrect query syntax, use <class>!<method> or just the class name'},
                    status='error',
                    exit_code=1,
                ),
                command='android hooking notify',
            )
        click.secho('Incorrect query syntax, please use <class>!<method> or just the class name', fg='red')
        return None

    api = state_connection.get_api()
    should_watch = _should_watch(args)
    dump_arguments = _should_dump_args(args)
    dump_backtrace = _should_dump_backtrace(args)
    dump_return = _should_dump_return_value(args)
    api.android_hooking_lazy_watch_for_pattern(query,
        should_watch, dump_arguments,
        dump_return,
        dump_backtrace)

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={
                    'action': 'watching_lazy',
                    'pattern': query,
                    'watch': should_watch,
                    'dump_args': dump_arguments,
                    'dump_backtrace': dump_backtrace,
                    'dump_return': dump_return,
                },
                warnings=['Lazy watch installed; hits arrive as async messages.',
                          'Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android hooking notify',
        )
    return None


def watch(args: list = None) -> Optional[CommandResult]:
    """
        Hook functions and print useful information when they are called.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 1:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing pattern'},
                    status='error',
                    human_text='Usage: android hooking watch <pattern> [--dump-args] [--dump-backtrace] [--dump-return]',
                    exit_code=1,
                ),
                command='android hooking watch',
            )
        click.secho('Usage: android hooking watch <package pattern> '
                    '(eg: com.example.test, *com.example*!*, com.example.test!toString)'
                    '(optional: --dump-args) '
                    '(optional: --dump-backtrace) '
                    '(optional: --dump-return)',
                    bold=True)
        return None

    query = args[0]
    if not _is_pattern_or_constant(query):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'incorrect query syntax, use <CLASS>!<METHOD> or class name'},
                    status='error',
                    exit_code=1,
                ),
                command='android hooking watch',
            )
        click.secho('Incorrect query syntax, please use <CLASS>!<METHOD>', fg='red')
        return None

    api = state_connection.get_api()
    api.android_hooking_watch(query,
                              _should_dump_args(args),
                              _should_dump_backtrace(args),
                              _should_dump_return_value(args))

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={
                    'action': 'watching',
                    'pattern': query,
                    'dump_args': _should_dump_args(args),
                    'dump_backtrace': _should_dump_backtrace(args),
                    'dump_return': _should_dump_return_value(args),
                },
                warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                          'Hook invocations arrive as async messages; poll via `agent state` or HTTP /events.'],
            ),
            command='android hooking watch',
        )
    return None


def search(args: list = None) -> Optional[CommandResult]:
    """
        Enumerates the current Android application for classes and methods.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing query'},
                    status='error',
                    human_text="Usage: android hooking search '<class>!<method>' [--json <filename>] [--only-classes]",
                    exit_code=1,
                ),
                command='android hooking search',
            )
        click.secho('Usage: android hooking search \'<class>!<method>\n\''
                    '(optional: --json <filename>)'
                    '(optional: --only-classes)', bold=True)
        return None

    query = args[0]

    if not _is_pattern_or_constant(query):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'incorrect query syntax, use <class>!<method>'},
                    status='error',
                    exit_code=1,
                ),
                command='android hooking search',
            )
        click.secho('Incorrect query syntax, please use <class>!<method>', fg='red')
        return None

    api = state_connection.get_api()
    results = api.android_hooking_enumerate(query)

    # Only get overloads if this flag is specified, otherwise just enumerating can be kind of slow
    target_file = _get_flag_value('--json', args)
    if should_output_json(args):
        for result in results:
            for _class in result['classes']:
                loader = result['loader']
                if loader is not None:
                    # <instance: java.lang.ClassLoader, $className: dalvik.system.PathClassLoader>
                    # but we only care about the className
                    start_index = loader.find('$className: ') + 12
                    start_part = loader[start_index:]
                    if start_part.find('>'):
                        end_index = start_part.find('>')
                    else:
                        end_index = start_part.find(' ')
                    loader = start_part[:end_index]

                _class['overloads'] = api.android_hooking_get_class_methods_overloads(_class['name'], _class['methods'],
                                                                                      loader)

        # --json <filename> 保留旧行为：写文件
        if target_file:
            results_json = {
                'meta': {
                    'runtime': 'java'
                },
                'data': results
            }
            with open(target_file, 'w') as fd:
                fd.write(json.dumps(results_json))
            return output_result(
                CommandResult(result={'dumped_to': target_file, 'count': len(results)}),
                command='android hooking search',
            )

        # 全局 JSON 模式（agent exec）：走统一输出层到 stdout
        return output_result(
            CommandResult(
                result={'runtime': 'java', 'results': results, 'count': len(results)},
                warnings=['overloads were fetched for every class; this can be slow.'],
            ),
            command='android hooking search',
        )

    # just print to the console
    for result in results:
        for _class in result['classes']:
            if _should_print_only_classes(args):
                print(_class['name'])
                continue

            for method in _class['methods']:
                print(f'{_class["name"]}.{method}')

    return None


def show_registered_broadcast_receivers(args: list = None) -> Optional[CommandResult]:
    """
        Enumerate all registered BroadcastReceivers

        :return:
    """

    api = state_connection.get_api()
    receivers = sorted(api.android_hooking_list_broadcast_receivers())

    if should_output_json(args):
        return output_result(
            CommandResult(result={'broadcast_receivers': receivers, 'count': len(receivers)}),
            command='android hooking list broadcast_receivers',
        )

    for class_name in receivers:
        click.secho(class_name)

    click.secho('\nFound {0} classes'.format(len(receivers)), bold=True)
    return None


def show_registered_services(args: list = None) -> Optional[CommandResult]:
    """
        Enumerate all registered Services

        :return:
    """

    api = state_connection.get_api()
    services = sorted(api.android_hooking_list_services())

    if should_output_json(args):
        return output_result(
            CommandResult(result={'services': services, 'count': len(services)}),
            command='android hooking list services',
        )

    for class_name in services:
        click.secho(class_name)

    click.secho('\nFound {0} classes'.format(len(services)), bold=True)
    return None


def show_registered_activities(args: list = None) -> Optional[CommandResult]:
    """
        Enumerate all registered Activities

        :return:
    """

    api = state_connection.get_api()
    activities = sorted(api.android_hooking_list_activities())

    if should_output_json(args):
        return output_result(
            CommandResult(result={'activities': activities, 'count': len(activities)}),
            command='android hooking list activities',
        )

    for class_name in activities:
        click.secho(class_name)

    click.secho('\nFound {0} classes'.format(len(activities)), bold=True)
    return None


def get_current_activity(args: list = None) -> Optional[CommandResult]:
    """
        Get the currently active activity

        :return:
    """

    api = state_connection.get_api()
    activity = api.android_hooking_get_current_activity()

    if should_output_json(args):
        return output_result(
            CommandResult(result=activity),
            command='android hooking get current_activity',
        )

    click.secho('Activity: {0}'.format(activity['activity']), bold=True)
    click.secho('Fragment: {0}'.format(activity['fragment']))
    return None


def set_method_return_value(args: list = None) -> Optional[CommandResult]:
    """
        Sets a Java methods return value to a specified boolean.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 2:
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'missing arguments'},
                    status='error',
                    human_text=('Usage: android hooking set return_value '
                                '"<fully qualified class method>" "<optional overload>" '
                                '(eg: "com.example.test.doLogin") <true/false>'),
                    exit_code=1,
                ),
                command='android hooking set return_value',
            )
        click.secho(('Usage: android hooking set return_value '
                     '"<fully qualified class method>" "<optional overload>" (eg: "com.example.test.doLogin") '
                     '<true/false>'),
                    bold=True)
        return None

    # make sure we got a true/false
    if args[-1].lower() not in ('true', 'false'):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'return value must be true or false'},
                    status='error',
                    exit_code=1,
                ),
                command='android hooking set return_value',
            )
        click.secho('Return value must be set to either true or false', bold=True)
        return None

    class_name = args[0].replace('\'', '"')  # fun!

    # check if we got an overload
    overload_filter = args[1].replace(' ', '') if len(args) == 3 else None
    retval = True if _string_is_true(args[-1]) else False

    api = state_connection.get_api()
    api.android_hooking_set_method_return(class_name,
                                          overload_filter,
                                          retval)

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={
                    'action': 'set_return_value',
                    'method': class_name,
                    'overload': overload_filter,
                    'value': retval,
                },
                warnings=['Hook installed; existing invocations are affected immediately.',
                          'Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android hooking set return_value',
        )
    return None
