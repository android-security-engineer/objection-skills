import unittest
from unittest import mock

from objection.commands.ios.keychain import dump, dump_raw, clear, add, \
    _data_flag_has_identifier, _get_flag_value, _should_do_smart_decode
from ...helpers import capture, normalize_table_whitespace
from objection.utils.output import should_output_json, set_json_output


class TestKeychain(unittest.TestCase):
    def setUp(self):
        # 确保全局 JSON 标志未置，命令级行为按 args 判定
        set_json_output(False)

    def tearDown(self):
        set_json_output(False)

    def test_should_output_json_in_arguments_returns_true(self):
        result = should_output_json(['--test', '--json'])
        self.assertTrue(result)

    def test_should_output_json_in_arguments_returns_false(self):
        result = should_output_json(['--test'])
        self.assertFalse(result)

    def test_dump_to_screen_handles_empty_data(self):
        with mock.patch('objection.state.connection.state_connection.get_api') as mock_api:
            mock_api.return_value.ios_keychain_list.return_value = []
            with capture(dump, []) as o:
                output = o

        self.assertIn('Created', output)

    def test_data_flag_check_ignored_without_data_flag(self):
        result = _data_flag_has_identifier(['--key', 'test_key'])
        self.assertTrue(result)

    def test_data_flag_is_checked_when_flag_is_specified(self):
        result = _data_flag_has_identifier(['--key', 'test_key', '--data', 'foo'])
        self.assertFalse(result)

    def test_data_flag_is_checked_when_only_data_flag_is_specified_without_key(self):
        result = _data_flag_has_identifier(['--data', 'foo'])
        self.assertFalse(result)

    def test_should_do_smart_decode_returns_true(self):
        result = _should_do_smart_decode(['--json', '--smart'])
        self.assertTrue(result)

    def test_should_do_smart_decode_returns_false(self):
        result = _should_do_smart_decode(['--json'])
        self.assertFalse(result)

    def test_get_flag_value_gets_value_of_flag(self):
        result = _get_flag_value(['--key', 'test_value'], '--key')
        self.assertEqual(result, 'test_value')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_dump_raw(self, mock_api):
        mock_api.return_value.ios_keychain_list_raw.return_value = []
        with capture(dump_raw, []) as o:
            _ = o
        self.assertTrue(mock_api.return_value.ios_keychain_list_raw.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.ios.keychain.open', create=True)
    def test_dump_to_json_file(self, mock_open, mock_api):
        """ 命令级 --json <filename> 仍写文件，并返回结构化确认。 """
        mock_api.return_value.ios_keychain_list.return_value = [
            {'access_control': '', 'account': '', 'create_date': '2018-07-21',
             'data': 'bar', 'item_class': 'kSecClassGeneric', 'service': 'foos'}]

        with capture(dump, ['--json', 'foo.json']) as o:
            output = o

        self.assertTrue(mock_open.called)
        # 仍打印进度提示
        self.assertIn('Writing keychain as json to foo.json...', output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_dump_global_json_returns_structured(self, mock_api):
        """ 全局 JSON 模式（agent exec）走统一输出层到 stdout。 """
        set_json_output(True)
        entries = [{'account': 'a', 'create_date': 'now', 'accessible_attribute': 'None',
                    'access_control': 'None', 'item_class': 'kSecClassGeneric',
                    'service': 's', 'data': 'd'}]
        mock_api.return_value.ios_keychain_list.return_value = entries

        with capture(dump, []) as o:
            output = o

        import json as _json
        payload = _json.loads(output[output.index('{'):])
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['command'], 'ios keychain dump')
        self.assertEqual(payload['result']['entries'], entries)
        self.assertEqual(payload['result']['count'], 1)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.ios.keychain.click.confirm')
    def test_clear(self, mock_confirm, mock_api):
        mock_confirm.return_value = True
        with capture(clear, []) as o:
            output = o
        self.assertEqual(output, 'Keychain cleared\n')
        self.assertTrue(mock_api.return_value.ios_keychain_empty.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_clear_global_json_skips_confirm(self, mock_api):
        """ JSON 模式下 clear 不应调用 click.confirm，直接清空。 """
        set_json_output(True)
        mock_api.return_value.ios_keychain_empty.return_value = None
        with capture(clear, []) as o:
            output = o
        self.assertNotIn('Are you sure', output)
        import json as _json
        payload = _json.loads(output[output.index('{'):])
        self.assertEqual(payload['result'], {'cleared': True})
        self.assertTrue(mock_api.return_value.ios_keychain_empty.called)

    def test_adds_item_validates_data_key_to_need_identifier(self):
        with capture(add, ['--data', 'test_data']) as o:
            output = o
        self.assertEqual(output, 'When specifying the --data flag, either --account or '
                                 '--service should also be added\n')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_adds_item_successfully(self, mock_api):
        mock_api.return_value.ios_keychain_add.return_value = True
        with capture(add, ['--account', 'test_key', '--data', 'test_data']) as o:
            output = o
        self.assertEqual(output, 'Successfully added the keychain item\n')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_adds_item_with_failure(self, mock_api):
        mock_api.return_value.ios_keychain_add.return_value = False
        with capture(add, ['--service', 'test_key', '--data', 'test_data']) as o:
            output = o
        self.assertEqual(output, 'Failed to add the keychain item\n')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_adds_item_global_json_returns_status(self, mock_api):
        set_json_output(True)
        mock_api.return_value.ios_keychain_add.return_value = True
        with capture(add, ['--service', 'test_key', '--data', 'test_data']) as o:
            output = o
        import json as _json
        payload = _json.loads(output[output.index('{'):])
        self.assertEqual(payload['status'], 'ok')
        self.assertEqual(payload['result'], {'added': True, 'account': None, 'service': 'test_key'})


if __name__ == '__main__':
    unittest.main()
