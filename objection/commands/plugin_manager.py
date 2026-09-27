import importlib.util
import os
import traceback
import uuid
from typing import Optional

import click

from ..utils.plugin import Plugin as PluginType
from objection.utils.output import CommandResult, output_result


def load_plugin(args: list = None) -> CommandResult:
    """
        Loads an objection plugin.

        :param args:
        :return:
    """

    if len(args) <= 0:
        human_text = 'Usage: plugin load <plugin path> (<plugin namespace>)'
        return output_result(
            CommandResult(status='error', result={'error': 'missing plugin path'},
                          human_text=human_text),
            command='plugin load',
        )

    path = os.path.abspath(args[0])
    if os.path.isdir(path):
        path = os.path.join(path, '__init__.py')

    if not os.path.exists(path):
        human_text = '[plugin] {0} does not appear to be a valid plugin. Missing __init__.py'.format(
            os.path.dirname(path))
        return output_result(
            CommandResult(status='error', result={'error': 'plugin path does not exist', 'path': path},
                          human_text=human_text),
            command='plugin load',
        )

    spec = importlib.util.spec_from_file_location(str(uuid.uuid4())[:8], path)
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)

    namespace = plugin.namespace
    if len(args) >= 2:
        namespace = args[1]

    plugin.__name__ = namespace

    # try and load the plugin (aka: run its __init__)
    try:

        instance = plugin.plugin(namespace)
        assert isinstance(instance, PluginType)

    except AssertionError:
        human_text = "Failed to load plugin '{0}'. Invalid plugin type.".format(namespace)
        return output_result(
            CommandResult(status='error', result={'error': 'invalid plugin type', 'namespace': namespace},
                          human_text=human_text),
            command='plugin load',
        )

    except Exception as e:
        human_text = "Failed to load plugin '{0}' with error: {1}\n{2}".format(
            namespace, str(e), traceback.format_exc())
        return output_result(
            CommandResult(status='error', result={'error': str(e), 'namespace': namespace,
                                                  'traceback': traceback.format_exc()},
                          human_text=human_text),
            command='plugin load',
        )

    from ..console import commands
    commands.COMMANDS['plugin']['commands'][instance.namespace] = instance.implementation
    human_text = 'Loaded plugin: {0}'.format(plugin.__name__)

    return output_result(
        CommandResult(result={'loaded': True, 'namespace': instance.namespace, 'path': path},
                      human_text=human_text),
        command='plugin load',
    )
