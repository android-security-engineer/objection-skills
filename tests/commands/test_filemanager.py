import unittest
from unittest import mock

from objection.commands.filemanager import cd, _path_exists_ios, _path_exists_android, pwd, pwd_print, _pwd_ios, \
    _pwd_android, ls, _ls_ios, _ls_android, download, _download_ios, _download_android, upload, rm, _rm_android
from objection.state.device import device_state, Ios, Android
from objection.state.filemanager import file_manager_state
from objection.utils.output import CommandResult
from ..helpers import capture, normalize_table_whitespace


class TestFileManager(unittest.TestCase):
    def tearDown(self):
        file_manager_state.cwd = None

    def test_cd_argument_validation(self):
        with capture(cd, []) as o:
            output = o

        self.assertEqual(output, 'Usage: cd <destination directory>\n')

    def test_cd_to_dot_directory_does_nothing(self):
        file_manager_state.cwd = '/foo'

        cd(['.'])

        self.assertEqual(file_manager_state.cwd, '/foo')

    def test_cd_to_double_dot_moves_up_one_directory(self):
        file_manager_state.cwd = '/foo/bar'

        with capture(cd, ['..']) as o:
            output = o

        self.assertEqual(output, '/foo\n')
        self.assertEqual(file_manager_state.cwd, '/foo')

    def test_cd_to_double_dot_moves_stays_in_current_directory_if_already_root(self):
        file_manager_state.cwd = '/'

        with capture(cd, ['..']) as o:
            output = o

        self.assertEqual(output, '/\n')
        self.assertEqual(file_manager_state.cwd, '/')

    @mock.patch('objection.commands.filemanager._path_exists_ios')
    def test_cd_to_absoluate_ios_path(self, mock_path_exists_ios):
        mock_path_exists_ios.return_value = True

        file_manager_state.cwd = '/foo'
        device_state.platform = Ios

        with capture(cd, ['/foo/bar/baz']) as o:
            output = o

        self.assertEqual(output, '/foo/bar/baz\n')
        self.assertEqual(file_manager_state.cwd, '/foo/bar/baz')

    @mock.patch('objection.commands.filemanager.os.path.isabs', return_value=False)
    @mock.patch('objection.commands.filemanager._path_exists_ios')
    def test_cd_treats_unix_style_path_as_absolute_when_host_is_windows(self, mock_path_exists_ios, _):
        mock_path_exists_ios.return_value = True

        file_manager_state.cwd = '/current'
        device_state.platform = Ios

        with capture(cd, ['/foo/bar']) as o:
            output = o

        self.assertEqual(output, '/foo/bar\n')
        self.assertEqual(file_manager_state.cwd, '/foo/bar')

    @mock.patch('objection.commands.filemanager._path_exists_android')
    def test_cd_to_absoluate_android_path(self, mock_path_exists_android):
        mock_path_exists_android.return_value = True

        file_manager_state.cwd = '/foo'
        device_state.platform = Android

        with capture(cd, ['/foo/bar/baz']) as o:
            output = o

        self.assertEqual(output, '/foo/bar/baz\n')
        self.assertEqual(file_manager_state.cwd, '/foo/bar/baz')

    @mock.patch('objection.commands.filemanager._path_exists_ios')
    def test_cd_to_absoluate_ios_path_that_does_not_exist(self, mock_path_exists_ios):
        mock_path_exists_ios.return_value = False

        file_manager_state.cwd = '/foo'
        device_state.platform = Ios

        with capture(cd, ['/foo/bar/baz']) as o:
            output = o

        self.assertEqual(output, 'Invalid path: `/foo/bar/baz`\n')
        self.assertEqual(file_manager_state.cwd, '/foo')

    @mock.patch('objection.commands.filemanager._path_exists_ios')
    def test_cd_to_relative_path_ios(self, mock_path_exists_ios):
        mock_path_exists_ios.return_value = True

        file_manager_state.cwd = '/foo'
        device_state.platform = Ios

        with capture(cd, ['bar']) as o:
            output = o

        self.assertEqual(output, '/foo/bar\n')
        self.assertEqual(file_manager_state.cwd, '/foo/bar')

    @mock.patch('objection.commands.filemanager._path_exists_android')
    def test_cd_to_relative_path_android(self, mock_path_exists_android):
        mock_path_exists_android.return_value = True

        file_manager_state.cwd = '/foo'
        device_state.platform = Android

        with capture(cd, ['bar']) as o:
            output = o

        self.assertEqual(output, '/foo/bar\n')
        self.assertEqual(file_manager_state.cwd, '/foo/bar')

    @mock.patch('objection.commands.filemanager._path_exists_ios')
    def test_cd_to_relative_path_ios_that_does_not_exist(self, mock_path_exists_ios):
        mock_path_exists_ios.return_value = False

        file_manager_state.cwd = '/foo'
        device_state.platform = Ios

        with capture(cd, ['bar']) as o:
            output = o

        self.assertEqual(output, 'Invalid path: `/foo/bar`\n')
        self.assertEqual(file_manager_state.cwd, '/foo')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_ios_path_exists_helper(self, mock_api):
        mock_api.return_value.ios_file_exists.return_value = True

        self.assertTrue(_path_exists_ios('/foo/bar'))

    def test_rm_dispatcher_validates_arguments(self):
        with capture(rm, []) as o:
            output = o

        expected = 'Usage: rm <target remote file>\n'

        self.assertEqual(output, expected)

    @mock.patch('objection.commands.filemanager.click.confirm')
    @mock.patch('objection.commands.filemanager._rm_android')
    def test_rm_dispatcher_confirms_before_delete(self, mock_android_rm, mock_confirm):
        device_state.platform = Android
        file_manager_state.cwd = '/foo'
        mock_confirm.return_value = False

        with capture(rm, ['poo']) as o:
            output = o

        expected = 'Not deleting /foo/poo\n'

        self.assertEqual(output, expected)
        self.assertFalse(mock_android_rm.called)

    @mock.patch('objection.commands.filemanager.click.confirm')
    @mock.patch('objection.commands.filemanager._rm_android')
    def test_rm_dispatcher_calls_android_rm_helper(self, mock_android_rm, mock_confirm):
        device_state.platform = Android
        mock_android_rm.return_value = True
        mock_confirm.return_value = True

        rm('/poo')

        self.assertTrue(mock_android_rm.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager._path_exists_android')
    def test_rm_android_helper_file_exists(self, mock_exists, mock_api):
        mock_exists.return_value = True
        mock_api.return_value.android_file_delete.return_value = True

        result = _rm_android('/poo')

        self.assertTrue(result)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_android_path_exists_helper(self, mock_api):
        mock_api.return_value.android_file_exists.return_value = True

        self.assertTrue(_path_exists_android('/foo/bar'))

    def test_returns_current_directory_via_helper_when_already_set(self):
        file_manager_state.cwd = '/foo'

        self.assertEqual(pwd(), '/foo')

    @mock.patch('objection.commands.filemanager._pwd_ios')
    def test_returns_current_directory_via_helper_for_ios(self, mock_pwd_ios):
        mock_pwd_ios.return_value = '/foo/bar'
        device_state.platform = Ios

        self.assertEqual(pwd(), '/foo/bar')
        self.assertTrue(mock_pwd_ios.called)

    @mock.patch('objection.commands.filemanager._pwd_android')
    def test_returns_current_directory_via_helper_for_android(self, mock_pwd_android):
        mock_pwd_android.return_value = '/foo/bar'
        device_state.platform = Android

        self.assertEqual(pwd(), '/foo/bar')
        self.assertTrue(mock_pwd_android.called)

    def test_prints_the_current_working_directory(self):
        file_manager_state.cwd = '/foo/bar/baz'

        with capture(pwd_print) as o:
            output = o

        self.assertEqual(output, 'Current directory: /foo/bar/baz\n')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_get_ios_pwd_via_helper(self, mock_api):
        mock_api.return_value.ios_file_cwd.return_value = '/foo/bar'

        self.assertEqual(_pwd_ios(), '/foo/bar')
        self.assertEqual(file_manager_state.cwd, '/foo/bar')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_get_android_pwd_via_helper(self, mock_api):
        mock_api.return_value.android_file_cwd.return_value = '/foo/baz'

        self.assertEqual(_pwd_android(), '/foo/baz')
        self.assertEqual(file_manager_state.cwd, '/foo/baz')

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager.pwd')
    @mock.patch('objection.commands.filemanager._ls_ios')
    def test_ls_gets_pwd_from_helper_with_no_argument(self, _, mock_pwd, mock_api):
        device_state.platform = Ios

        ls([])

        self.assertTrue(mock_pwd.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager._ls_ios')
    def test_ls_calls_ios_helper_method(self, mock_ls_ios, mock_get_api):
        device_state.platform = Ios

        ls(['/foo/bar'])

        self.assertTrue(mock_ls_ios.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager._ls_ios')
    def test_ls_treats_unix_style_path_as_absolute_when_host_is_windows(self, mock_ls_ios, mock_api):
        device_state.platform = Ios
        file_manager_state.cwd = '/current'
        mock_api.return_value.ios_file_ls.return_value = {
            'readable': True,
            'writable': True,
            'files': {}
        }
        mock_ls_ios.return_value = 'mocked listing'

        ls(['/foo/bar'])

        self.assertTrue(mock_ls_ios.called)
        args = mock_ls_ios.call_args[0]
        self.assertEqual(args[0], '/foo/bar')
        self.assertIsInstance(args[1], dict)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager._ls_android')
    def test_ls_calls_android_helper_method(self, mock_ls_android, mock_get_api):
        device_state.platform = Android

        ls(['/foo/bar'])

        self.assertTrue(mock_ls_android.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_lists_readable_ios_directory_using_helper_method(self, mock_api):
        mock_api.return_value.ios_file_ls.return_value = {
            'path': '/foo/bar',
            'readable': True,
            'writable': False,
            'files': {
                'test': {
                    'fileName': 'test',
                    'readable': True,
                    'writable': False,
                    'attributes': {
                        'NSFileType': 'A',
                        'NSFilePosixPermissions': 'B',
                        'NSFileProtectionKey': 'C',
                        'NSFileOwnerAccountName': 'D',
                        'NSFileOwnerAccountID': 'E',
                        'NSFileGroupOwnerAccountName': 'F',
                        'NSFileGroupOwnerAccountID': 'G',
                        'NSFileSize': 123918204914,
                        'NSFileCreationDate': 'H'
                    }
                }
            }
        }

        data = mock_api.return_value.ios_file_ls.return_value
        human_text = _ls_ios('/foo/bar', data)

        for token in ('NSFileType', 'Perms', 'NSFileProtection', 'Read', 'Write',
                      'Owner', 'Group', 'Size', 'Creation', 'Name',
                      'A', 'B', 'C', 'D (E)', 'F (G)', '115.4 GiB', 'H', 'test',
                      'Readable: True  Writable: False'):
            self.assertIn(token, human_text)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_lists_readable_ios_directory_using_helper_method_no_attributes(self, mock_api):
        mock_api.return_value.ios_file_ls.return_value = {
            'path': '/foo/bar',
            'readable': True,
            'writable': True,
            'files': {
                'test': {
                    'fileName': 'test',
                    'readable': True,
                    'writable': True,
                    'attributes': {}
                }
            }
        }

        data = mock_api.return_value.ios_file_ls.return_value
        human_text = _ls_ios('/foo/bar', data)

        for token in ('NSFileType', 'Perms', 'NSFileProtection', 'Read', 'Write',
                      'Owner', 'Group', 'Size', 'Creation', 'Name',
                      'n/a', 'n/a (n/a)', 'test',
                      'Readable: True  Writable: True'):
            self.assertIn(token, human_text)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_lists_unreadable_ios_directory_using_helper_method(self, mock_api):
        mock_api.return_value.ios_file_ls.return_value = {
            'path': '/foo/bar',
            'readable': False,
            'writable': False,
            'files': {}
        }

        data = mock_api.return_value.ios_file_ls.return_value
        human_text = _ls_ios('/foo/bar', data)

        self.assertEqual(human_text, '\nReadable: False  Writable: False')

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_lists_readable_android_directory_using_helper_method(self, mock_api):
        mock_api.return_value.android_file_ls.return_value = {
            'path': '/foo/bar',
            'readable': True,
            'writable': True,
            'files': {
                'test': {
                    'fileName': 'test',
                    'readable': True,
                    'writable': True,
                    'attributes': {
                        'isDirectory': False,
                        'isFile': True,
                        'isHidden': False,
                        'lastModified': 1507189001000,
                        'size': 249,
                    }
                }
            }
        }

        data = mock_api.return_value.android_file_ls.return_value
        human_text = _ls_android('/foo/bar', data)

        for token in ('Type', 'Last Modified', 'Read', 'Write', 'Hidden', 'Size', 'Name',
                      'File', '2017-10-05 07:36:41 GMT', 'True', 'False', '249.0 B', 'test',
                      'Readable: True  Writable: True'):
            self.assertIn(token, human_text)

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_lists_unreadable_android_directory_using_helper_method(self, mock_api):
        mock_api.return_value.android_file_ls.return_value = {
            'path': '/foo/bar',
            'readable': False,
            'writable': False,
            'files': {}
        }

        human_text = _ls_android('/foo/bar', mock_api.return_value.android_file_ls.return_value)

        self.assertEqual(human_text, '\nReadable: False  Writable: False')

    def test_download_platform_proxy_validates_arguments(self):
        with capture(download, []) as o:
            output = o

        self.assertEqual(output, 'Usage: filesystem download <remote location> (optional: <local destination>)\n')

    @mock.patch('objection.commands.filemanager._download_ios')
    def test_download_platform_proxy_calls_ios_method(self, mock_download_ios):
        device_state.platform = Ios

        download(['/foo', '/bar'])

        self.assertTrue(mock_download_ios.called)

    @mock.patch('objection.commands.filemanager._download_android')
    def test_download_platform_proxy_calls_android_method(self, mock_download_android):
        device_state.platform = Android

        download(['/foo', '/bar'])

        self.assertTrue(mock_download_android.called)

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager.open', create=True)
    def test_downloads_file_with_ios_helper(self, mock_open, mock_api):
        mock_api.return_value.ios_file_readable.return_value = True
        mock_api.return_value.ios_file_path_is_file.return_value = True
        mock_api.return_value.ios_file_download.return_value = {'data': b'\x00'}

        file_manager_state.cwd = '/foo'

        result = _download_ios('/foo', '/bar', False)

        self.assertTrue(mock_open.called)
        self.assertEqual(result['status'], 'ok')
        self.assertIn('Successfully downloaded /foo to /bar', result['message'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_downloads_file_but_fails_on_unreadable_with_ios_helper(self, mock_api):
        mock_api.return_value.ios_file_readable.return_value = False

        result = _download_ios('/foo', '/bar', False)

        self.assertEqual(result['status'], 'error')
        self.assertIn('Unable to download file. File is not readable.', result['message'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    def test_downloads_file_but_fails_on_file_type_with_ios_helper(self, mock_api):
        mock_api.return_value.ios_file_readable.return_value = True
        mock_api.return_value.ios_file_path_is_file.return_value = False

        result = _download_ios('/foo', '/bar', False)

        self.assertEqual(result['status'], 'skipped')
        self.assertIn('To download folders, specify --folder.', result['message'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager.open', create=True)
    def test_downloads_file_with_android_helper(self, mock_open, mock_api):
        mock_api.return_value.android_file_readable.return_value = True
        mock_api.return_value.android_file_path_is_file.return_value = True
        mock_api.return_value.android_file_download.return_value = {'data': b'\x00'}

        file_manager_state.cwd = '/foo'

        result = _download_android('/foo', '/bar', False)

        self.assertTrue(mock_open.called)
        self.assertEqual(result['status'], 'ok')
        self.assertIn('Successfully downloaded /foo to /bar', result['message'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager.open', create=True)
    def test_downloads_file_but_fails_on_unreadable_with_android_helper(self, mock_open, mock_api):
        mock_api.return_value.android_file_readable.return_value = False

        file_manager_state.cwd = '/foo'

        result = _download_android('/foo', '/bar', False)

        self.assertFalse(mock_open.called)
        self.assertEqual(result['status'], 'error')
        self.assertIn('Unable to download file. Target path is not readable.', result['message'])

    @mock.patch('objection.state.connection.state_connection.get_api')
    @mock.patch('objection.commands.filemanager.open', create=True)
    def test_downloads_file_but_fails_on_file_type_with_android_helper(self, mock_open, mock_api):
        mock_api.return_value.android_file_readable.return_value = True
        mock_api.return_value.android_file_path_is_file.return_value = False

        file_manager_state.cwd = '/foo'

        result = _download_android('/foo', '/bar', False)

        self.assertFalse(mock_open.called)
        self.assertEqual(result['status'], 'skipped')
        self.assertIn('To download folders, specify --folder.', result['message'])

    def test_file_upload_method_proxy_validates_arguments(self):
        with capture(upload, []) as o:
            output = o

        self.assertEqual(output, 'Usage: filesystem upload <local source> (optional: <remote destination>)\n')

    @mock.patch('objection.commands.filemanager._upload_ios')
    def test_file_upload_method_proxy_calls_ios_helper_method(self, mock_upload_ios):
        device_state.platform = Ios

        upload(['/foo', '/bar'])

        self.assertTrue(mock_upload_ios.called)

    @mock.patch('objection.commands.filemanager._upload_android')
    def test_file_upload_method_proxy_calls_android_helper_method(self, mock_upload_android):
        device_state.platform = Android

        upload(['/foo', '/bar'])

        self.assertTrue(mock_upload_android.called)
