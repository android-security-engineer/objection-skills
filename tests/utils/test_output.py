import unittest
from unittest import mock

from objection.utils.output import (
    CommandResult, output_result, error_result, should_output_json,
    set_json_output, is_json_output, push_result_capture, pop_result_capture,
)
from objection.utils.events import record_event, drain_events, peek_events
from ..helpers import capture


class TestCommandResult(unittest.TestCase):
    def test_to_dict_shape(self):
        r = CommandResult(result={'a': 1}, status='ok', warnings=['w'])
        d = r.to_dict('cmd')
        self.assertEqual(set(d.keys()), {'status', 'command', 'result', 'jobs_created', 'warnings'})
        self.assertEqual(d['command'], 'cmd')
        self.assertEqual(d['result'], {'a': 1})
        self.assertEqual(d['warnings'], ['w'])

    def test_defaults(self):
        r = CommandResult()
        self.assertEqual(r.status, 'ok')
        self.assertEqual(r.exit_code, 0)
        self.assertEqual(r.jobs_created, [])
        self.assertEqual(r.warnings, [])

    def test_error_result_helper(self):
        r = error_result('boom', 'cmd', 2)
        self.assertEqual(r.status, 'error')
        self.assertEqual(r.result, {'error': 'boom'})
        self.assertEqual(r.exit_code, 2)
        self.assertEqual(r.human_text, 'boom')


class TestOutputRendering(unittest.TestCase):
    def setUp(self):
        set_json_output(False)

    def tearDown(self):
        set_json_output(False)

    def test_json_mode_emits_envelope(self):
        set_json_output(True)
        with capture(output_result, CommandResult(result={'x': 1}), 'cmd') as o:
            import json as _json
            payload = _json.loads(o)
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['command'], 'cmd')
        self.assertEqual(payload['result'], {'x': 1})

    def test_human_mode_prints_human_text(self):
        with capture(output_result, CommandResult(human_text='hello there'), 'cmd') as o:
            self.assertEqual(o, 'hello there\n')

    def test_human_mode_prints_warnings(self):
        with capture(output_result, CommandResult(human_text='ok', warnings=['careful']), 'cmd') as o:
            self.assertIn('Warning: careful', o)

    def test_should_output_json_respects_global_flag(self):
        self.assertFalse(should_output_json([]))
        set_json_output(True)
        self.assertTrue(should_output_json([]))
        set_json_output(False)

    def test_should_output_json_respects_arg_flag(self):
        self.assertTrue(should_output_json(['--json', 'foo.json']))
        self.assertFalse(should_output_json(['--nope']))


class TestResultCapture(unittest.TestCase):
    def setUp(self):
        set_json_output(True)

    def tearDown(self):
        set_json_output(False)
        # 清理可能残留的捕获栈
        while pop_result_capture() is not None:
            pass

    def test_capture_intercepts_output(self):
        buf = push_result_capture()
        output_result(CommandResult(result={'a': 1}), 'cmd1')
        output_result(CommandResult(result={'b': 2}, status='error'), 'cmd2')
        captured = pop_result_capture()

        self.assertEqual(len(captured), 2)
        self.assertEqual(captured[0]['result'], {'a': 1})
        self.assertEqual(captured[1]['status'], 'error')
        self.assertEqual(captured[1]['command'], 'cmd2')

    def test_capture_does_not_print(self):
        buf = push_result_capture()
        with capture(output_result, CommandResult(result={'a': 1}), 'cmd') as o:
            self.assertEqual(o, '')  # 捕获模式不打印
        pop_result_capture()

    def test_pop_when_empty_returns_none(self):
        self.assertIsNone(pop_result_capture())


class TestEventBuffer(unittest.TestCase):
    def setUp(self):
        set_json_output(True)
        drain_events()

    def tearDown(self):
        set_json_output(False)
        drain_events()

    def test_record_and_drain(self):
        record_event({'type': 'send', 'payload': {'class': 'Foo'}})
        record_event({'type': 'send', 'payload': {'class': 'Bar'}})
        d = drain_events()
        self.assertEqual(len(d['events']), 2)
        self.assertEqual(d['events'][0]['message']['payload']['class'], 'Foo')
        self.assertEqual(d['remaining'], 0)

    def test_drain_clears_buffer(self):
        record_event({'type': 'send'})
        drain_events()
        d2 = drain_events()
        self.assertEqual(d2['events'], [])

    def test_peek_does_not_clear(self):
        record_event({'type': 'send'})
        p = peek_events()
        self.assertEqual(len(p['events']), 1)
        self.assertEqual(p['remaining'], 1)
        # 仍可 drain
        d = drain_events()
        self.assertEqual(len(d['events']), 1)

    def test_record_ignored_in_human_mode(self):
        set_json_output(False)
        record_event({'type': 'send'})
        d = drain_events()
        self.assertEqual(d['events'], [])


if __name__ == '__main__':
    unittest.main()
