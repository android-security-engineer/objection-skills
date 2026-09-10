import unittest
from unittest import mock

from objection.api.app import create_app


class TestAgentHttpEndpoints(unittest.TestCase):
    def setUp(self):
        from objection.utils.output import set_json_output
        set_json_output(False)
        self.addCleanup(lambda: set_json_output(False))
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_capabilities_no_device_needed(self):
        r = self.client.get('/capabilities')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('commands', data['result'])
        self.assertIsInstance(data['result']['commands'], list)
        self.assertTrue(len(data['result']['commands']) > 0)

    def test_events_poll_empty(self):
        r = self.client.get('/events/poll')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['result']['events'], [])
        self.assertEqual(data['result']['dropped'], 0)

    def test_events_peek_does_not_clear(self):
        from objection.utils.events import record_event, drain_events
        from objection.utils.output import set_json_output
        set_json_output(True)
        drain_events()
        record_event({'type': 'send', 'payload': {'k': 'v'}})
        try:
            r = self.client.get('/events/poll?peek=1')
            data = r.get_json()
            self.assertEqual(len(data['result']['events']), 1)
            # peek 后仍可 drain
            r2 = self.client.get('/events/poll')
            self.assertEqual(len(r2.get_json()['result']['events']), 1)
        finally:
            set_json_output(False)
            drain_events()

    def test_state_returns_503_without_agent(self):
        with mock.patch('objection.api.agent_endpoints.state_connection') as sc:
            sc.agent = None
            r = self.client.get('/state')
        self.assertEqual(r.status_code, 503)
        data = r.get_json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('no agent', data['result']['error'])

    def test_command_exec_requires_json_body(self):
        r = self.client.post('/command/exec', data='not json')
        self.assertNotEqual(r.status_code, 200)

    def test_command_exec_no_agent_returns_503(self):
        with mock.patch('objection.api.agent_endpoints.state_connection') as sc:
            sc.agent = None
            r = self.client.post('/command/exec', json={'command': 'env'})
        self.assertEqual(r.status_code, 503)

    def test_command_exec_runs_command(self):
        """ 模拟已连接 agent，执行一条已改造命令，验证返回结构化结果。 """
        with mock.patch('objection.api.agent_endpoints.state_connection') as sc, \
                mock.patch('objection.console.repl.Repl') as MockRepl:
            sc.agent = mock.MagicMock()
            sc.get_agent.return_value = mock.MagicMock(pid=1234)
            # 模拟 repl.run_command 会触发 output_result（被捕获器截获）
            def fake_run(cmd):
                from objection.utils.output import output_result, CommandResult
                output_result(CommandResult(result={'echo': cmd}), command=cmd)
            MockRepl.return_value.run_command.side_effect = fake_run

            r = self.client.post('/command/exec', json={'command': 'android hooking list classes'})

        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['command'], 'android hooking list classes')
        self.assertEqual(data['result'], {'echo': 'android hooking list classes'})

    def test_agent_rpc_unknown_method(self):
        """ 调用不存在的 RPC 方法应返回 500 + error。 """
        class EmptyApi:
            pass
        with mock.patch('objection.api.agent_endpoints.state_connection') as sc:
            sc.agent = mock.MagicMock()
            sc.get_api.return_value = EmptyApi()
            r = self.client.get('/agent/rpc/nonexistent_method')
        self.assertEqual(r.status_code, 500)
        data = r.get_json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('unknown RPC method', data['result']['error'])

    def test_agent_rpc_calls_method_with_args(self):
        """ POST /agent/rpc/<m> 应以 JSON 数组为位置参数调用 RPC。 """
        called = {}
        class FakeApi:
            def my_method(self, *args):
                called['args'] = args
                return {'sum': sum(args)}
        with mock.patch('objection.api.agent_endpoints.state_connection') as sc:
            sc.agent = mock.MagicMock()
            sc.get_api.return_value = FakeApi()
            r = self.client.post('/agent/rpc/my_method', json=[1, 2, 3])
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['result'], {'sum': 6})
        self.assertEqual(called['args'], (1, 2, 3))


if __name__ == '__main__':
    unittest.main()
