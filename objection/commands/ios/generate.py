import os

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result


def clazz(args: list) -> CommandResult:
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

    return output_result(
        CommandResult(result={'source': source, 'asset': 'objchookmanager.js'},
                      human_text=source),
        command='ios hooking generate class',
    )


def simple(args: list) -> CommandResult:
    """
        Generate simple hooks for all methods in a class.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(status='error', result={'error': 'missing class name'},
                          human_text='Usage: ios hooking generate simple <class name>'),
            command='ios hooking generate simple',
        )

    classname = args[0]

    api = state_connection.get_api()
    methods = api.ios_hooking_get_class_methods(classname, False)

    if len(methods) <= 0:
        return output_result(
            CommandResult(status='error', result={'error': 'no class / methods found', 'class': classname},
                          human_text='No class / methods found'),
            command='ios hooking generate simple',
        )

    hooks = []
    human_lines = ["var target = ObjC.classes.{};".format(classname)]
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

        hooks.append(hook)
        human_lines.append(hook)

    return output_result(
        CommandResult(result={'class': classname, 'methods': methods, 'hooks': hooks},
                      human_text=''.join(human_lines)),
        command='ios hooking generate simple',
    )
