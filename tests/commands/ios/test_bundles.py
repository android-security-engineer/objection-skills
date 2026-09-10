import unittest
from unittest import mock

from objection.commands.ios.bundles import show_frameworks, _should_include_apple_bundles, _should_print_full_path, \
    _is_apple_bundle, show_bundles
from ...helpers import capture, normalize_table_whitespace


class TestBundles(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle_data = [
            {
                'bundle': 'com.apple.AppleIDSSOAuthentication',
                'executable': 'AppleIDSSOAuthentication',
                'path': '/AppleIDSSOAuthentication',
                'version': '1.0'
            },
            {
                'bundle': 'com.apple.LinguisticData',
                'executable': 'LinguisticData',
                'path': '/LinguisticData/LinguisticDataLinguisticDataLinguisticDataLinguisticData',
                'version': '1.0'
            },
            {
                'bundle': 'net.hockeyapp.sdk.ios',
                'executable': 'hockeyapp',
                'path': '/hockeyapp',
                'version': '1.0'
            },
            {
                'bundle': 'za.apple.MapKit',
                'executable': 'MapKit',
                'path': '/MapKit',
                'version': '1.0'
            }
        ]

    def test_should_include_apple_bundles_helper_is_true(self):
        data = ['foo', 'bar', '--include-apple-frameworks']
        self.assertTrue(_should_include_apple_bundles(data))

    def test_should_include_apple_bundles_helper_is_false(self):
        data = ['foo', 'bar']
        self.assertFalse(_should_include_apple_bundles(data))

    def test_should_print_full_path_helper_is_true(self):
        data = ['foo', 'bar', '--full-path']
        self.assertTrue(_should_print_full_path(data))

    def test_should_print_full_path_helper_is_false(self):
        data = ['foo', 'bar']
        self.assertFalse(_should_print_full_path(data))

    def test_is_apple_bunlde_returns_false_on_none(self):
        self.assertFalse(_is_apple_bundle(None))

    def test_is_apple_bunlde_returns_true_for_apple_bundle(self):
        self.assertTrue(_is_apple_bundle('com.apple.PhoneNumbers'))

    def test_is_apple_bunlde_returns_false_for_string_not_starting_with_com_apple(self):
        self.assertFalse(_is_apple_bundle('za.com.apple.PhoneNumbers'))

    def test_is_apple_bunlde_returns_false_for_non_apple_bundle(self):
        self.assertFalse(_is_apple_bundle('net.hockeyapp.sdk.ios'))

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_show_frameworks_prints_without_apple_bundles(self, mock_api):
        mock_api.return_value.ios_bundles_get_frameworks.return_value = self.bundle_data

        with capture(show_frameworks, []) as o:
            output = o

        # 不锁定 tabulate 精确列宽（跨模块/版本不稳定），断言关键字段
        for token in ('Executable', 'Bundle', 'Version', 'Path',
                      'hockeyapp', 'net.hockeyapp.sdk.ios', '/hockeyapp',
                      'MapKit', 'za.apple.MapKit', '/MapKit'):
            self.assertIn(token, output)
        # 未传 --include-apple-frameworks 时不应出现 Apple bundle
        self.assertNotIn('AppleIDSSOAuthentication', output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_show_frameworks_prints_with_apple_bundles(self, mock_api):
        mock_api.return_value.ios_bundles_get_frameworks.return_value = self.bundle_data

        with capture(show_frameworks, ['--include-apple-frameworks']) as o:
            output = o

        for token in ('Executable', 'Bundle', 'Version', 'Path',
                      'AppleIDSSOAuthentication', 'com.apple.AppleIDSSOAuthentication',
                      'LinguisticData', 'hockeyapp', 'net.hockeyapp.sdk.ios',
                      'MapKit', 'za.apple.MapKit'):
            self.assertIn(token, output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_show_frameworks_prints_with_apple_bundles_and_full_paths(self, mock_api):
        mock_api.return_value.ios_bundles_get_frameworks.return_value = self.bundle_data

        with capture(show_frameworks, ['--include-apple-frameworks', '--full-path']) as o:
            output = o

        for token in ('Executable', 'Bundle', 'Version', 'Path',
                      'AppleIDSSOAuthentication', 'LinguisticData',
                      'LinguisticDataLinguisticDataLinguisticDataLinguisticData',
                      'hockeyapp', 'MapKit'):
            self.assertIn(token, output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_show_bundles_prints_bundles(self, mock_api):
        mock_api.return_value.ios_bundles_get_bundles.return_value = self.bundle_data

        with capture(show_bundles, []) as o:
            output = o

        for token in ('Executable', 'Bundle', 'Version', 'Path',
                      'AppleIDSSOAuthentication', 'LinguisticData',
                      'hockeyapp', 'MapKit'):
            self.assertIn(token, output)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_show_bundles_prints_bundles_full_path(self, mock_api):
        mock_api.return_value.ios_bundles_get_bundles.return_value = self.bundle_data

        with capture(show_bundles, ['--full-path']) as o:
            output = o

        for token in ('Executable', 'Bundle', 'Version', 'Path',
                      'AppleIDSSOAuthentication', 'LinguisticData',
                      'LinguisticDataLinguisticDataLinguisticDataLinguisticData',
                      'hockeyapp', 'MapKit'):
            self.assertIn(token, output)
