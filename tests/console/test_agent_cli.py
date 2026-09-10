import unittest
from unittest import mock

from objection.console.agent_cli import _enumerate_capabilities
from objection.console.commands import COMMANDS
from ..helpers import capture


class TestEnumerateCapabilities(unittest.TestCase):
    def test_enumerates_top_level_commands(self):
        caps = _enumerate_capabilities(COMMANDS)
        names = [c['name'] for c in caps]
        self.assertIn('android', names)
        self.assertIn('ios', names)
        self.assertIn('memory', names)

    def test_recursive_subcommands(self):
        caps = _enumerate_capabilities(COMMANDS)
        android = next(c for c in caps if c['name'] == 'android')
        self.assertIn('subcommands', android)
        sub_names = [s['name'] for s in android['subcommands']]
        self.assertIn('android hooking', sub_names)

    def test_has_exec_flag(self):
        caps = _enumerate_capabilities(COMMANDS)
        # pwd 应是可执行叶子
        pwd_cap = next(c for c in caps if c['name'] == 'pwd')
        self.assertTrue(pwd_cap['has_exec'])

    def test_entry_shape(self):
        caps = _enumerate_capabilities(COMMANDS)
        for entry in caps:
            self.assertIn('name', entry)
            self.assertIn('meta', entry)
            self.assertIn('has_exec', entry)


class TestAgentCapabilitiesCommand(unittest.TestCase):
    def test_capabilities_outputs_full_envelope(self):
        """ capabilities 命令应强制 JSON 并输出完整统一 schema。 """
        from objection.console.agent_cli import agent_capabilities
        from objection.utils.output import set_json_output
        set_json_output(False)
        # agent_capabilities 被 @agent.command 装饰为 click Command，调 .callback 绕过 click 解析
        callback = agent_capabilities.callback if hasattr(agent_capabilities, 'callback') else agent_capabilities
        try:
            with capture(callback) as o:
                import json as _json
                payload = _json.loads(o)
            self.assertEqual(payload['status'], 'ok')
            self.assertEqual(payload['command'], 'agent capabilities')
            self.assertIn('commands', payload['result'])
            self.assertIsInstance(payload['result']['commands'], list)
        finally:
            set_json_output(False)


if __name__ == '__main__':
    unittest.main()
