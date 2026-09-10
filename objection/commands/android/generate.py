import os
from typing import Optional

import click

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def clazz(args: list) -> Optional[CommandResult]:
    """
        Simply echoes the source for a generic Hook Manager
        sample for Objective-C hooks with Frida.

        :param args:
        :return:
    """

    js_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '../../utils/assets', 'javahookmanager.js'
    )

    with open(js_path, 'r') as f:
        source = f.read()

    return output_result(
        CommandResult(
            result={'source': source, 'asset': 'javahookmanager.js'},
            human_text=source if not should_output_json(args) else None,
        ),
        command='android hooking generate class',
    )


def simple(args: list) -> Optional[CommandResult]:
    """
        Generate simple hooks for all methods in a Java class.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(
                status='error',
                result={'error': 'missing class name'},
                human_text='Usage: android hooking generate simple <class name>',
                exit_code=1,
            ),
            command='android hooking generate simple',
        )

    classname = args[0]

    api = state_connection.get_api()
    methods = api.android_hooking_get_class_methods(classname, False)

    if len(methods) <= 0:
        return output_result(
            CommandResult(
                status='error',
                result={'error': 'no class / methods found', 'class': classname},
                human_text='No class / methods found',
                exit_code=1,
            ),
            command='android hooking generate simple',
        )

    # nasty! :D
    unique_methods = set([x.split('(')[0].split('.')[-1] for x in methods])
    json_mode = should_output_json(args)

    hooks = []
    for method in unique_methods:
        hook = """
Java.perform(function() {
    var clazz = Java.use('{clazz}');
    clazz.{method}.implementation = function() {

        //

        return clazz.{method}.apply(this, arguments);
    }
});
""".replace('{clazz}', classname).replace('{method}', method)
        hooks.append(hook)

    human_text = None
    if not json_mode:
        human_text = '\n'.join(hooks)

    return output_result(
        CommandResult(
            result={'class': classname, 'methods': sorted(unique_methods), 'hooks': hooks},
            human_text=human_text,
        ),
        command='android hooking generate simple',
    )
