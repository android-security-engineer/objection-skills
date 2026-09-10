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
        '../../utils/assets', 'objchookmanager.js'
    )

    with open(js_path, 'r') as f:
        source = f.read()
        if not should_output_json(args):
            click.secho(source, dim=True)

    if should_output_json(args):
        return output_result(
            CommandResult(result={'source': source, 'asset': 'objchookmanager.js'}),
            command='ios hooking generate class',
        )
    return None


def simple(args: list) -> Optional[CommandResult]:
    """
        Generate simple hooks for all methods in a class.

        :param args:
        :return:
    """

    if len(args) <= 0:
        click.secho('Usage: ios hooking generate simple <class name>', bold=True)
        if should_output_json(args):
            return output_result(
                CommandResult(status='error', result={'error': 'missing class name'}),
                command='ios hooking generate simple',
            )
        return None

    classname = args[0]

    api = state_connection.get_api()
    methods = api.ios_hooking_get_class_methods(classname, False)

    if len(methods) <= 0:
        click.secho('No class / methods found')
        if should_output_json(args):
            return output_result(
                CommandResult(status='error', result={'error': 'no class / methods found', 'class': classname}),
                command='ios hooking generate simple',
            )
        return None

    click.secho("var target = ObjC.classes.{};".format(classname), dim=True)

    json_mode = should_output_json(args)
    hooks = []
    for method in methods:
        hook = """
Interceptor.attach(target['{method}'].implementation, {{
  onEnter: function (args) {{
    console.log('Entering {method}!');
  }},
  onLeave: function (retval) {{
    console.log('Leaving {method}');
  }},
}});
""".replace('{method}', method)

        if not json_mode:
            click.secho(hook, dim=True)
        hooks.append(hook)

    if json_mode:
        return output_result(
            CommandResult(result={'class': classname, 'methods': methods, 'hooks': hooks}),
            command='ios hooking generate simple',
        )
    return None
