import json
from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.helpers import clean_argument_flags
from objection.utils.output import CommandResult, output_result


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


def show_android_classes(args: list = None) -> CommandResult:
    """
        Show the currently loaded classes.
        Note that Java classes are only loaded when they are used,
        so not all classes may be present.

        :return:
    """

    api = state_connection.get_api()
    classes = sorted(api.android_hooking_get_classes())

    human_lines = list(classes)
    human_lines.append('\nFound {0} classes'.format(len(classes)))
    return output_result(
        CommandResult(
            result={'classes': classes, 'count': len(classes)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list classes',
    )


def show_android_class_loaders(args: list = None) -> CommandResult:
    """
        Show the currently registered class loaders.

        :return:
    """

    api = state_connection.get_api()
    loaders = sorted(api.android_hooking_get_class_loaders())

    human_lines = ['* {0}'.format(loader) for loader in loaders]
    human_lines.append('\nFound {0} class loaders'.format(len(loaders)))
    return output_result(
        CommandResult(
            result={'class_loaders': loaders, 'count': len(loaders)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list class_loaders',
    )


def show_android_class_methods(args: list = None) -> CommandResult:
    """
        Shows the methods available on an Android class.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing class name'},
                status='error',
                human_text='Usage: android hooking list class_methods <class name>',
                exit_code=1,
            ),
            command='android hooking list class_methods',
        )

    class_name = args[0]

    api = state_connection.get_api()
    methods = sorted(api.android_hooking_get_class_methods(class_name))

    human_lines = [method for method in methods]
    human_lines.append('\nFound {0} method(s)'.format(len(methods)))
    return output_result(
        CommandResult(
            result={'class': class_name, 'methods': methods, 'count': len(methods)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list class_methods',
    )


def notify(args: list = None) -> CommandResult:
    """
        Notify when a class becomes available.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing pattern'},
                status='error',
                human_text='Usage: android hooking notify <pattern>',
                exit_code=1,
            ),
            command='android hooking notify',
        )

    query = args[0]
    if not _is_pattern_or_constant(query):
        return output_result(
            CommandResult(
                result={'error': 'incorrect query syntax, use <class>!<method> or just the class name'},
                status='error',
                exit_code=1,
            ),
            command='android hooking notify',
        )

    api = state_connection.get_api()
    should_watch = _should_watch(args)
    dump_arguments = _should_dump_args(args)
    dump_backtrace = _should_dump_backtrace(args)
    dump_return = _should_dump_return_value(args)
    api.android_hooking_lazy_watch_for_pattern(query,
        should_watch, dump_arguments,
        dump_return,
        dump_backtrace)

    human_text = 'Watching for pattern: {0}'.format(query)
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
            human_text=human_text,
            warnings=['Lazy watch installed; hits arrive as async messages.',
                      'Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android hooking notify',
    )


def watch(args: list = None) -> CommandResult:
    """
        Hook functions and print useful information when they are called.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing pattern'},
                status='error',
                human_text='Usage: android hooking watch <pattern> [--dump-args] [--dump-backtrace] [--dump-return]',
                exit_code=1,
            ),
            command='android hooking watch',
        )

    query = args[0]
    if not _is_pattern_or_constant(query):
        return output_result(
            CommandResult(
                result={'error': 'incorrect query syntax, use <CLASS>!<METHOD> or class name'},
                status='error',
                exit_code=1,
            ),
            command='android hooking watch',
        )

    api = state_connection.get_api()
    api.android_hooking_watch(query,
                              _should_dump_args(args),
                              _should_dump_backtrace(args),
                              _should_dump_return_value(args))

    human_text = 'Watching: {0}'.format(query)
    return output_result(
        CommandResult(
            result={
                'action': 'watching',
                'pattern': query,
                'dump_args': _should_dump_args(args),
                'dump_backtrace': _should_dump_backtrace(args),
                'dump_return': _should_dump_return_value(args),
            },
            human_text=human_text,
            warnings=['Job id not surfaced; use `agent state` to list running jobs.',
                      'Hook invocations arrive as async messages; poll via `agent state` or HTTP /events.'],
        ),
        command='android hooking watch',
    )


def search(args: list = None) -> CommandResult:
    """
        Enumerates the current Android application for classes and methods.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing query'},
                status='error',
                human_text="Usage: android hooking search '<class>!<method>' [--json <filename>] [--only-classes]",
                exit_code=1,
            ),
            command='android hooking search',
        )

    query = args[0]

    if not _is_pattern_or_constant(query):
        return output_result(
            CommandResult(
                result={'error': 'incorrect query syntax, use <class>!<method>'},
                status='error',
                exit_code=1,
            ),
            command='android hooking search',
        )

    api = state_connection.get_api()
    results = api.android_hooking_enumerate(query)

    # Only get overloads if this flag is specified, otherwise just enumerating can be kind of slow
    target_file = _get_flag_value('--json', args)
    for result in results:
        for _class in result['classes']:
            loader = result['loader']
            if loader is not None:
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

    if _should_print_only_classes(args):
        classes = [_class['name'] for result in results for _class in result['classes']]
        return output_result(
            CommandResult(result={'runtime': 'java', 'classes': classes, 'count': len(classes)}),
            command='android hooking search',
        )

    human_items = []
    for result in results:
        for _class in result['classes']:
            for method in _class['methods']:
                human_items.append('{0}.{1}'.format(_class['name'], method))

    return output_result(
        CommandResult(
            result={'runtime': 'java', 'results': results, 'count': len(results)},
            human_text='\n'.join(human_items),
            warnings=['overloads were fetched for every class; this can be slow.'],
        ),
        command='android hooking search',
    )


def show_registered_broadcast_receivers(args: list = None) -> CommandResult:
    """
        Enumerate all registered BroadcastReceivers

        :return:
    """

    api = state_connection.get_api()
    receivers = sorted(api.android_hooking_list_broadcast_receivers())

    human_lines = list(receivers)
    human_lines.append('\nFound {0} classes'.format(len(receivers)))
    return output_result(
        CommandResult(
            result={'broadcast_receivers': receivers, 'count': len(receivers)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list broadcast_receivers',
    )


def show_registered_services(args: list = None) -> CommandResult:
    """
        Enumerate all registered Services

        :return:
    """

    api = state_connection.get_api()
    services = sorted(api.android_hooking_list_services())

    human_lines = list(services)
    human_lines.append('\nFound {0} classes'.format(len(services)))
    return output_result(
        CommandResult(
            result={'services': services, 'count': len(services)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list services',
    )


def show_registered_activities(args: list = None) -> CommandResult:
    """
        Enumerate all registered Activities

        :return:
    """

    api = state_connection.get_api()
    activities = sorted(api.android_hooking_list_activities())

    human_lines = list(activities)
    human_lines.append('\nFound {0} classes'.format(len(activities)))
    return output_result(
        CommandResult(
            result={'activities': activities, 'count': len(activities)},
            human_text='\n'.join(human_lines),
        ),
        command='android hooking list activities',
    )


def get_current_activity(args: list = None) -> CommandResult:
    """
        Get the currently active activity

        :return:
    """

    api = state_connection.get_api()
    activity = api.android_hooking_get_current_activity()

    human_text = 'Activity: {0}\nFragment: {1}'.format(activity.get('activity'), activity.get('fragment'))
    return output_result(
        CommandResult(result=activity, human_text=human_text),
        command='android hooking get current_activity',
    )


def set_method_return_value(args: list = None) -> CommandResult:
    """
        Sets a Java methods return value to a specified boolean.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 2:
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

    # make sure we got a true/false
    if args[-1].lower() not in ('true', 'false'):
        return output_result(
            CommandResult(
                result={'error': 'return value must be true or false'},
                status='error',
                human_text='return value must be true or false',
                exit_code=1,
            ),
            command='android hooking set return_value',
        )

    class_name = args[0].replace('\'', '"')  # fun!

    # check if we got an overload
    overload_filter = args[1].replace(' ', '') if len(args) == 3 else None
    retval = True if _string_is_true(args[-1]) else False

    api = state_connection.get_api()
    api.android_hooking_set_method_return(class_name,
                                          overload_filter,
                                          retval)

    human_text = 'Set return value for {0} to {1}'.format(class_name, retval)
    return output_result(
        CommandResult(
            result={
                'action': 'set_return_value',
                'method': class_name,
                'overload': overload_filter,
                'value': retval,
            },
            human_text=human_text,
            warnings=['Hook installed; existing invocations are affected immediately.',
                      'Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android hooking set return_value',
    )
