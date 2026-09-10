import json as _json
import unittest
from unittest import mock

from objection.utils.output import set_json_output
from ..helpers import capture


def _payload(output):
    """从可能含人类前缀的输出里提取 JSON envelope。"""
    return _json.loads(output[output.index('{'):])


class TestUiJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)

    @mock.patch('objection.commands.ui._alert_ios')
    def test_alert_json(self, mock_alert_ios):
        from objection.commands.ui import alert
        from objection.state.device import device_state, Ios
        device_state.platform = Ios()
        try:
            with capture(alert, ['hello']) as o:
                payload = _payload(o)
            self.assertEqual(payload['status'], 'ok')
            self.assertEqual(payload['result']['message'], 'hello')
        finally:
            device_state.platform = None

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_dump_ios_ui_json(self, mock_api):
        from objection.commands.ui import dump_ios_ui
        mock_api.return_value.ios_ui_window_dump.return_value = '<window/>'
        with capture(dump_ios_ui, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['ui'], '<window/>')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_bypass_touchid_json(self, mock_api):
        from objection.commands.ui import bypass_touchid
        with capture(bypass_touchid, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['action'], 'bypass_touchid')
        self.assertTrue(payload['warnings'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_android_flag_secure_json_validates(self, mock_api):
        from objection.commands.ui import android_flag_secure
        with capture(android_flag_secure, ['bogus']) as o:
            payload = _payload(o)
        self.assertEqual(payload['status'], 'error')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_android_flag_secure_json(self, mock_api):
        from objection.commands.ui import android_flag_secure
        with capture(android_flag_secure, ['true']) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['value'], 'true')


class TestAndroidShellExecJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_execute_json(self, mock_api):
        from objection.commands.android.command import execute
        mock_api.return_value.android_shell_exec.return_value = {'stdOut': 'uid=0', 'stdErr': ''}
        with capture(execute, ['id']) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['command'], 'id')
        self.assertEqual(payload['result']['stdout'], 'uid=0')


class TestAndroidIntentsJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_launch_activity_json(self, mock_api):
        from objection.commands.android.intents import launch_activity
        with capture(launch_activity, ['com.example.MainActivity']) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['activity'], 'com.example.MainActivity')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_launch_activity_json_validates(self, mock_api):
        from objection.commands.android.intents import launch_activity
        with capture(launch_activity, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['status'], 'error')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_analyze_implicit_intents_json(self, mock_api):
        from objection.commands.android.intents import analyze_implicit_intents
        with capture(analyze_implicit_intents, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['action'], 'analyze_implicit_intents')
        self.assertTrue(payload['warnings'])


class TestIosBinaryJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_info_json(self, mock_api):
        from objection.commands.ios.binary import info
        mock_api.return_value.ios_binary_info.return_value = {
            'App': {'type': 'Mach-O', 'encrypted': False, 'pie': True, 'arc': True,
                    'canary': True, 'stackExec': False, 'rootSafe': False}}
        with capture(info, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['count'], 1)
        self.assertIn('App', payload['result']['binaries'])


class TestGenerateJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_android_simple_json(self, mock_api):
        from objection.commands.android.generate import simple
        mock_api.return_value.android_hooking_get_class_methods.return_value = ['foo()', 'bar()']
        with capture(simple, ['com.example.Cls']) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['class'], 'com.example.Cls')
        self.assertEqual(len(payload['result']['hooks']), 2)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_android_simple_json_validates(self, mock_api):
        from objection.commands.android.generate import simple
        with capture(simple, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['status'], 'error')


class TestCommandHistoryJson(unittest.TestCase):
    def setUp(self):
        set_json_output(True)
        from objection.state.app import app_state
        self._app_state = app_state
        self._orig = list(app_state.successful_commands)
        app_state.successful_commands = ['env', 'android hooking list classes']

    def tearDown(self):
        set_json_output(False)
        self._app_state.successful_commands = self._orig

    def test_history_json(self):
        from objection.commands.command_history import history
        with capture(history, []) as o:
            payload = _payload(o)
        self.assertEqual(payload['result']['count'], 2)
        self.assertEqual(payload['result']['commands'], ['env', 'android hooking list classes'])

    def test_clear_json(self):
        from objection.commands.command_history import clear
        with capture(clear, []) as o:
            payload = _payload(o)
        self.assertTrue(payload['result']['cleared'])


if __name__ == '__main__':
    unittest.main()
