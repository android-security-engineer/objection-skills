import os
import tempfile
import time


import click
from tabulate import tabulate

from ..state.connection import state_connection
from ..state.device import device_state, Ios, Android
from ..state.filemanager import file_manager_state
from ..utils.helpers import sizeof_fmt
from ..utils.output import CommandResult, output_result, should_output_json
from ..utils.helpers import is_unix_absolute_path

# variable used to cache entries from the ls-like
# commands used in the below helpers. only used
# by the _get_short_*_listing methods.
_ls_cache = {}

def _should_download_folder(args: list) -> bool:
    """
        Checks if --json is in the list of tokens received from the command line.

        :param args:
        :return:
    """

    return len(args) > 0 and '--folder' in args

def cd(args: list) -> CommandResult:
    """
        Change the current working directory of the device.

        While this method does not actually change any directories,
        it simply updates the value in the file_manager_state property
        that keeps record of the current directory.

        Before changing directories though, some checks are performed
        on the device to at least ensure that the destination directory
        exists.

        :param args:
        :return:
    """

    if len(args) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing destination directory'},
                status='error',
                human_text='Usage: cd <destination directory>',
                exit_code=1,
            ),
            command='cd',
        )

    path = args[0]
    current_dir = pwd()

    # nothing to do
    if path == '.':
        return output_result(
            CommandResult(result={'cwd': current_dir, 'changed': False}),
            command='cd',
        )

    # moving one directory back
    device_path_separator = device_state.platform.path_separator

    if path == '..' or path == '..'+device_path_separator:

        split_path = os.path.split(current_dir)

        # nothing to do if we are already at root
        if len(split_path) == 1:
            return output_result(
                CommandResult(result={'cwd': current_dir, 'changed': False, 'at_root': True}),
                command='cd',
            )

        new_path = ''.join(split_path[:-1])

        file_manager_state.cwd = new_path

        return output_result(
            CommandResult(result={'cwd': new_path, 'changed': True},
                          human_text=new_path),
            command='cd',
        )

    # if we got an absolute path, check if the path
    # actually exists, and then cd to it if we can
    if is_unix_absolute_path(path):

        # assume the path does not exist by default
        does_exist = False

        # normalise path to remove '../'
        if '..'+device_path_separator in path:
            path = os.path.normpath(path).replace('\\', device_path_separator)

        # check for existence based on the runtime
        if device_state.platform == Ios:
            does_exist = _path_exists_ios(path)

        if device_state.platform == Android:
            does_exist = _path_exists_android(path)

        # if we checked with the device that the path exists
        # and it did, update the state manager, otherwise
        # show an error that the path may be invalid
        if does_exist:

            file_manager_state.cwd = path
            return output_result(
                CommandResult(result={'cwd': path, 'changed': True},
                              human_text=path),
                command='cd',
            )

        return output_result(
            CommandResult(
                result={'error': 'invalid path', 'path': path},
                status='error',
                human_text='Invalid path: `{0}`'.format(path),
                exit_code=1,
            ),
            command='cd',
        )

    # directory is not absolute, tack it on at the end and
    # see if its legit.
    else:

        proposed_path = device_path_separator.join([current_dir, path])

        # normalise path to remove '../'
        if '..'+device_path_separator in proposed_path:
            proposed_path = os.path.normpath(proposed_path).replace('\\', device_path_separator)
            if proposed_path == '//':
                return output_result(
                    CommandResult(result={'cwd': current_dir, 'changed': False}),
                    command='cd',
                )

        # assume the proposed_path does not exist by default
        does_exist = False

        # check for existence based on the runtime
        if device_state.platform == Ios:
            does_exist = _path_exists_ios(proposed_path)

        if device_state.platform == Android:
            does_exist = _path_exists_android(proposed_path)

        # if we checked with the device that the path exists
        # and it did, update the state manager, otherwise
        # show an error that the path may be invalid
        if does_exist:

            file_manager_state.cwd = proposed_path
            return output_result(
                CommandResult(result={'cwd': proposed_path, 'changed': True},
                              human_text=proposed_path),
                command='cd',
            )

        return output_result(
            CommandResult(
                result={'error': 'invalid path', 'path': proposed_path},
                status='error',
                human_text='Invalid path: `{0}`'.format(proposed_path),
                exit_code=1,
            ),
            command='cd',
        )

def path_exists(path: str) -> bool:
    """
        Checks if a path exists on remote device.

        :param path:
        :return:
    """

    if device_state.platform == Ios:
        return _path_exists_ios(path)

    if device_state.platform == Android:
        return _path_exists_android(path)

def _path_exists_ios(path: str) -> bool:
    """
        Checks an iOS device if a path exists.

        :param path:
        :return:
    """

    api = state_connection.get_api()
    return api.ios_file_exists(path)

def _path_exists_android(path: str) -> bool:
    """
        Checks an Android device if a path exists.

        :param path:
        :return:
    """

    api = state_connection.get_api()
    return api.android_file_exists(path)

def pwd(args: list = None) -> str:
    """
        Return the current working directory.

        If a record exists in the filemanager state, that directory
        is returned. Else, an environment specific call is made to
        the device to determine the directory it considers itself
        to be working from.

        :param args:
        :return:
    """

    if file_manager_state.cwd is not None:
        return file_manager_state.cwd

    if device_state.platform == Ios:
        return _pwd_ios()

    if device_state.platform == Android:
        return _pwd_android()

def pwd_print(args: list = None) -> CommandResult:
    """
        Prints the current working directory.

        :param args:
        :return:
    """

    cwd = pwd()
    return output_result(
        CommandResult(result={'cwd': cwd}, human_text='Current directory: {0}'.format(cwd)),
        command='pwd',
    )

def _pwd_ios() -> str:
    """
        Execute a Frida hook that gets the current working
        directory from an iOS device.

        :return:
    """

    api = state_connection.get_api()
    cwd = api.ios_file_cwd()

    # update the file_manager state's cwd
    file_manager_state.cwd = cwd

    return cwd

def _pwd_android() -> str:
    """
        Execute a Frida hook that gets the current working
        directory from an Android device.

        :return:
    """

    api = state_connection.get_api()
    cwd = api.android_file_cwd()

    # update the file_manager state's cwd
    file_manager_state.cwd = cwd

    return cwd

def ls(args: list) -> CommandResult:
    """
        Get a directory listing for a path on a device.
        If no path is provided, the current working directory is used.

        :param args:
        :return:
    """

    # check if we have received a path to ls for.
    if len(args) <= 0:
        path = pwd()
    else:
        path = args[0]
        if not is_unix_absolute_path(path):
            path = device_state.platform.path_separator.join([pwd(), path])

    api = state_connection.get_api()
    if device_state.platform == Ios:
        data = api.ios_file_ls(path)
    elif device_state.platform == Android:
        data = api.android_file_ls(path)
    else:
        return output_result(
            CommandResult(result={'error': 'unknown platform'}, status='error', exit_code=1),
            command='ls',
        )

    if device_state.platform == Ios:
        human_text = _ls_ios(path, data)

    if device_state.platform == Android:
        human_text = _ls_android(path, data)

    return output_result(
        CommandResult(
            result={'path': path, 'readable': data.get('readable'),
                    'writable': data.get('writable'), 'files': data.get('files')},
            human_text=human_text,
        ),
        command='ls',
    )

def _ls_ios(path: str, data: dict = None) -> str:
    """
        List files implementation for iOS.

        See:
            http://www.stanford.edu/class/cs193p/cgi-bin/drupal/system/files/lectures/09_Data.pdf

        :param path:
        :param data:
        :return:
    """

    api = state_connection.get_api()
    if data is None:
        data = api.ios_file_ls(path)

    def _get_key_if_exists(attribs, key):
        """
            Small helper to grab keys where some may or may
            not exist in the file attributes.

            :param attribs:
            :param key:
            :return:
        """

        if key in attribs:
            return attribs[key]

        return 'n/a'

    def _humanize_size_if_possible(size: str) -> str:
        """
            Small helper method used to 'humanize' file sizes
            if the file size is not recorded as 'n/a'

            :param size:
            :return:
        """

        return sizeof_fmt(int(size)) if size != 'n/a' else 'n/a'

    # if the directory was readable, dump the filesystem listing
    # and attributes to screen.
    human_text = tabulate(
        [[
            _get_key_if_exists(file_data['attributes'], 'NSFileType').replace('NSFileType', ''),
            _get_key_if_exists(file_data['attributes'], 'NSFilePosixPermissions'),
            _get_key_if_exists(file_data['attributes'], 'NSFileProtectionKey').replace('NSFileProtection', ''),

            # file read / write permissions
            file_data['readable'],
            file_data['writable'],

            # owner name and uid
            _get_key_if_exists(file_data['attributes'], 'NSFileOwnerAccountName') + ' (' +
            _get_key_if_exists(file_data['attributes'], 'NSFileOwnerAccountID') + ')',

            # group name and gid
            _get_key_if_exists(file_data['attributes'], 'NSFileGroupOwnerAccountName') + ' (' +
            _get_key_if_exists(file_data['attributes'], 'NSFileGroupOwnerAccountID') + ')',

            _humanize_size_if_possible(_get_key_if_exists(file_data['attributes'], 'NSFileSize')),
            _get_key_if_exists(file_data['attributes'], 'NSFileCreationDate'),

            file_name,

        ] for file_name, file_data in data['files'].items()], headers=[
            'NSFileType', 'Perms', 'NSFileProtection', 'Read', 'Write', 'Owner', 'Group', 'Size', 'Creation', 'Name'
        ],
    ) if data['readable'] else ''

    # handle the permissions summary for this directory
    human_text += '\nReadable: {0}  Writable: {1}'.format(data['readable'], data['writable'])
    return human_text

def _ls_android(path: str, data: dict = None) -> str:
    """
        Lit files implementation for Android devices.

        :param path:
        :param data:
        :return:
    """

    api = state_connection.get_api()
    if data is None:
        data = api.android_file_ls(path)

    def _timestamp_to_str(stamp: str) -> str:
        """
            Small helper method to convert the timestamps we get
            from the Android filesystem to human readable ones.

            :param stamp:
            :return:
        """

        # convert the time to an integer
        stamp = int(stamp)

        if stamp > 0:
            return time.strftime('%Y-%m-%d %H:%M:%S GMT', time.gmtime(stamp / 1000.0))

        return 'n/a'

    human_text = tabulate(
        [[
            'Directory' if file_data['attributes']['isDirectory'] else 'File',

            _timestamp_to_str(file_data['attributes']['lastModified']),

            # read / write permissions
            file_data['readable'],
            file_data['writable'],
            file_data['attributes']['isHidden'],

            sizeof_fmt(float(file_data['attributes']['size'])),

            file_name,

        ] for file_name, file_data in data['files'].items()], headers=[
            'Type', 'Last Modified', 'Read', 'Write', 'Hidden', 'Size', 'Name'
        ],
    ) if data['readable'] else ''

    human_text += '\nReadable: {0}  Writable: {1}'.format(data['readable'], data['writable'])
    return human_text

def download(args: list) -> CommandResult:
    """
        Downloads a file from a remote filesystem and stores
        it locally.

        This method is simply a proxy to the actual download methods
        used for the appropriate environment.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing remote location'},
                status='error',
                human_text='Usage: filesystem download <remote location> (optional: <local destination>)',
                exit_code=1,
            ),
            command='filesystem download',
        )

    # determine the source and destination file names.
    # if we didnt get a specification of where to dump the file,
    # assume the same name should be used locally.
    source = args[0]
    should_download_folder = _should_download_folder(args)
    # If the user specified a destination, use it. Otherwise, use the basename of the source.
    if len(args) > (1 + should_download_folder):
        destination = args[1]
    else:
        destination = os.path.basename(source)

    download_result = None
    if device_state.platform == Ios:
        download_result = _download_ios(source, destination, should_download_folder)

    if device_state.platform == Android:
        download_result = _download_android(source, destination, should_download_folder)

    if isinstance(download_result, dict) and download_result.get('status') == 'error':
        return output_result(
            CommandResult(
                result={'error': download_result.get('message'), 'source': source, 'destination': destination},
                status='error',
                human_text=download_result.get('message'),
                exit_code=1,
            ),
            command='filesystem download',
        )

    return output_result(
        CommandResult(
            result={'action': 'downloaded', 'source': source, 'destination': destination,
                    'folder': should_download_folder},
            human_text='Downloaded {0} to {1}'.format(source, destination),
        ),
        command='filesystem download',
    )

def _download_ios(path: str, destination: str, should_download_folder: bool, path_root: bool = True) -> dict:
    """
        Download a file from an iOS filesystem and store it locally.

        :param path:
        :param destination:
        :return:
    """

    # if the path we got is not absolute, join it with the
    # current working directory
    if not is_unix_absolute_path(path):
        path = device_state.platform.path_separator.join([pwd(), path])

    api = state_connection.get_api()

    if path_root:
        human_text = 'Downloading {0} to {1}'.format(path, destination)

    if not api.ios_file_readable(path):
        return {'status': 'error', 'message': 'Unable to download file. File is not readable.', 'path': path}

    if not api.ios_file_path_is_file(path):
        if not should_download_folder:
            return {'status': 'skipped', 'message': 'To download folders, specify --folder.', 'path': path}

        if os.path.exists(destination):
            return {'status': 'skipped', 'message': 'The target path already exists.', 'path': path}

        os.makedirs(destination)

        if path_root:
            if should_output_json(None):
                human_text = 'Directory download confirmed in non-interactive mode.'
            else:
                if not click.confirm('Do you want to download the full directory?', default=True):
                    return {'status': 'aborted', 'message': 'Download aborted.', 'path': path}

        data = api.ios_file_ls(path)
        results = []
        for name, _ in data['files'].items():
            sub_path = device_state.platform.path_separator.join([path, name])
            sub_destination = os.path.join(destination, name)
            results.append(_download_ios(sub_path, sub_destination, True, False))
        return {'status': 'ok', 'message': 'Recursive download finished.', 'results': results}

    file_data = api.ios_file_download(path)
    with open(destination, 'wb') as fh:
        fh.write(bytearray(file_data['data']))

    human_text = 'Successfully downloaded {0} to {1}'.format(path, destination)
    return {'status': 'ok', 'message': human_text, 'path': path}

def _download_android(path: str, destination: str, should_download_folder: bool, path_root: bool = True) -> dict:
    """
        Download a file from the Android filesystem and store it locally.

        :param path:
        :param destination:
        :return:
    """

    # if the path we got is not absolute, join it with the
    # current working directory
    if not is_unix_absolute_path(path):
        path = device_state.platform.path_separator.join([pwd(), path])

    api = state_connection.get_api()

    if path_root:
        human_text = 'Downloading {0} to {1}'.format(path, destination)

    if not api.android_file_readable(path):
        return {'status': 'error', 'message': 'Unable to download file. Target path is not readable.', 'path': path}

    if not api.android_file_path_is_file(path):
        if not should_download_folder:
            return {'status': 'skipped', 'message': 'To download folders, specify --folder.', 'path': path}

        if os.path.exists(destination):
            return {'status': 'skipped', 'message': 'The target path already exists.', 'path': path}

        os.makedirs(destination)

        if path_root:
            if should_output_json(None):
                human_text = 'Directory download confirmed in non-interactive mode.'
            else:
                if not click.confirm('Do you want to download the full directory?', default=True):
                    return {'status': 'aborted', 'message': 'Download aborted.', 'path': path}

        data = api.android_file_ls(path)
        results = []
        for name, _ in data['files'].items():
            sub_path = device_state.platform.path_separator.join([path, name])
            sub_destination = os.path.join(destination, name)
            results.append(_download_android(sub_path, sub_destination, True, False))
        return {'status': 'ok', 'message': 'Recursive download finished.', 'results': results}

    file_data = api.android_file_download(path)
    with open(destination, 'wb') as fh:
        fh.write(bytearray(file_data['data']))

    human_text = 'Successfully downloaded {0} to {1}'.format(path, destination)
    return {'status': 'ok', 'message': human_text, 'path': path}

def upload(args: list) -> CommandResult:
    """
        Uploads a local file to the remote operating system.

        This method is just a proxy method to the real upload
        method used based on the runtime that is available.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing local source'},
                status='error',
                human_text='Usage: filesystem upload <local source> (optional: <remote destination>)',
                exit_code=1,
            ),
            command='filesystem upload',
        )

    source = args[0]
    destination = args[1] if len(args) > 1 else device_state.platform.path_separator.join(
        [pwd(), os.path.basename(source)])

    messages = []
    if device_state.platform == Ios:
        messages.extend(_upload_ios(source, destination))

    if device_state.platform == Android:
        messages.extend(_upload_android(source, destination))

    human_text = '\n'.join(messages) if messages else 'Uploaded {0} to {1}'.format(source, destination)
    return output_result(
        CommandResult(
            result={'action': 'uploaded', 'source': source, 'destination': destination},
            human_text=human_text,
        ),
        command='filesystem upload',
    )

def _upload_ios(path: str, destination: str) -> list:
    """
        Upload a file to a remote iOS filesystem.

        :param path:
        :param destination:
        :return: list of status messages
    """

    messages = []

    if not is_unix_absolute_path(destination):
        destination = device_state.platform.path_separator.join([pwd(), destination])

    api = state_connection.get_api()
    messages.append('Uploading {0} to {1}'.format(path, destination))

    # if we cant read the file, just stop
    if not api.ios_file_writable(os.path.dirname(destination)):
        messages.append('Unable to upload file. Destination is not writable.')
        return messages

    messages.append('Reading source file...')
    with open(path, 'rb') as f:
        data = f.read().hex()

    messages.append('Sending file to device for writing...')
    api.ios_file_upload(destination, data)

    messages.append('Uploaded: {0}'.format(destination))

    # unset the cache key for this directory so the next short listing
    # will have updated contents
    if os.path.dirname(destination) in _ls_cache:
        del _ls_cache[os.path.dirname(destination)]

    return messages

def _upload_android(path: str, destination: str) -> list:
    """
        Upload a file to a remote Android filesystem.

        :param path:
        :param destination:
        :return: list of status messages
    """

    messages = []

    if not is_unix_absolute_path(destination):
        destination = device_state.platform.path_separator.join([pwd(), destination])

    api = state_connection.get_api()
    messages.append('Uploading {0} to {1}'.format(path, destination))

    # if we cant read the file, just stop
    if not api.android_file_writable(os.path.dirname(destination)):
        messages.append('Unable to upload file. Destination is not writable.')
        return messages

    messages.append('Reading source file...')
    with open(path, 'rb') as f:
        data = f.read().hex()

    messages.append('Sending file to device for writing...')
    api.android_file_upload(destination, data)

    messages.append('Uploaded: {0}'.format(destination))

    # unset the cache key for this directory so the next short listing
    # will have updated contents
    if os.path.dirname(destination) in _ls_cache:
        del _ls_cache[os.path.dirname(destination)]

    return messages

def rm(args: list) -> CommandResult:
    """
        Remove a file from the remote filesystem.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing target file'},
                status='error',
                human_text='Usage: rm <target remote file>',
                exit_code=1,
            ),
            command='rm',
        )

    target = args[0]

    if not is_unix_absolute_path(target):
        target = device_state.platform.path_separator.join([pwd(), target])

    # human mode 下保留交互确认
    if should_output_json(args):
        # Agent/JSON 模式下直接执行，不阻塞
        pass
    else:
        if not click.confirm('Really delete {0} ?'.format(target)):
            return output_result(
                CommandResult(result={'action': 'deleted', 'target': target, 'deleted': False},
                              human_text='Not deleting {0}'.format(target)),
                command='rm',
            )

    deleted = False
    if device_state.platform == Ios:
        deleted = _rm_ios(target)

    if device_state.platform == Android:
        deleted = _rm_android(target)

    return output_result(
        CommandResult(result={'action': 'deleted', 'target': target, 'deleted': bool(deleted)},
                      human_text='{0} successfully deleted'.format(target) if deleted else '{0} does not exist'.format(target)),
        command='rm',
    )

def _rm_android(t: str) -> bool:
    """
        Removes a file from an Android device.

        :param t:
        :return:
    """

    api = state_connection.get_api()

    if not _path_exists_android(t):
        return False

    deleted = api.android_file_delete(t)

    # update the file system cache entry
    if os.path.dirname(t) in _ls_cache:
        del _ls_cache[os.path.dirname(t)]

    return bool(deleted)

def _rm_ios(t: str) -> bool:
    """
        Removes a file from an iOS device.

        :param t:
        :return:
    """

    api = state_connection.get_api()

    if not _path_exists_ios(t):
        return False

    deleted = api.ios_file_delete(t)

    # update the file system cache entry
    if os.path.dirname(t) in _ls_cache:
        del _ls_cache[os.path.dirname(t)]

    return bool(deleted)

def cat(args: list) -> CommandResult:
    """
        Downloads a file from a remote filesystem and echos
        it's contents

        This method is simply a proxy to the relevant download methods
        that echoes the contents and cleans up after itself.

        :param args:
        :return:
    """

    if len(args) < 1:
        return output_result(
            CommandResult(
                result={'error': 'missing remote location'},
                status='error',
                human_text='Usage: filesystem cat <remote location>',
                exit_code=1,
            ),
            command='filesystem cat',
        )

    # determine the source and destination file names.
    # if we didnt get a specification of where to dump the file,
    # assume the same name should be used locally.
    source = args[0]
    _, destination = tempfile.mkstemp('.file')

    if device_state.platform == Ios:
        _download_ios(source, destination, False)

    if device_state.platform == Android:
        _download_android(source, destination, False)

    with open(destination, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    os.remove(destination)

    return output_result(
        CommandResult(result={'path': source, 'content': content},
                      human_text='====\n{0}\n===='.format(content)),
        command='filesystem cat',
    )

def _get_short_ios_listing() -> list:
    """
        Get a shortened file and directory listing for
        iOS devices.

        :return:
    """

    # default to the pwd. this method is for tab
    # completions anyways.
    directory = pwd()

    # the response for this directory
    resp = []

    # check our cheap cache if we have a listing
    if directory in _ls_cache:
        return _ls_cache[directory]

    api = state_connection.get_api()
    data = api.ios_file_ls(directory)

    # loop the response, marking entries as either being
    # a file or a directory. this response will be stored
    # in the _ls_cache too.
    for name, attribs in data['files'].items():

        # attributes key contains the type
        attributes = attribs['attributes']

        # if the attributes dict does not have the file type,
        # just continue as we cant be sure what it is.
        if 'NSFileType' not in attributes:
            continue

        # append a tuple with name, type
        resp.append((name, 'directory' if attributes['NSFileType'] == 'NSFileTypeDirectory' else 'file'))

    # cache the response so its faster next time!
    _ls_cache[directory] = resp

    # grab the output lets seeeeee
    return resp

def _get_short_android_listing() -> list:
    """
        Get a shortened file and directory listing for
        Android devices.

        :return:
    """

    # default to the pwd. this method is for tab
    # completions anyways.
    directory = pwd()

    # the response for this directory
    resp = []

    # check our cheap cache if we have a listing
    if directory in _ls_cache:
        return _ls_cache[directory]

    api = state_connection.get_api()
    data = api.android_file_ls(directory)

    # loop the response, marking entries as either being
    # a file or a directory. this response will be stored
    # in the _ls_cache too.
    for name, attribs in data['files'].items():
        attributes = attribs['attributes']

        # append a tuple with name, type
        resp.append((name, 'directory' if attributes['isDirectory'] else 'file'))

    # cache the response so its faster next time!
    _ls_cache[directory] = resp

    # grab the output lets seeeeee
    return resp

def list_folders_in_current_fm_directory() -> dict:
    """
        Return folders in the current working directory of the
        Frida attached device.
    """

    resp = {}

    # get the folders based on the runtime
    if device_state.platform == Ios:
        response = _get_short_ios_listing()

    elif device_state.platform == Android:
        response = _get_short_android_listing()

    # looks like we landed in an unknown runtime.
    # just return.
    else:
        return resp

    # loop the response to get entries for the 'directory'
    # type.
    for entry in response:
        file_name, file_type = entry

        if file_type == 'directory':
            if ' ' in file_name:
                resp[f"'{file_name}'"] = file_name
            else:
                resp[file_name] = file_name

    return resp

def list_files_in_current_fm_directory() -> dict:
    """
        Return files in the current working directory of the
        Frida attached device.
    """

    resp = {}

    # check for existence based on the runtime
    if device_state.platform == Ios:
        response = _get_short_ios_listing()

    elif device_state.platform == Android:
        response = _get_short_android_listing()

    # looks like we landed in an unknown runtime.
    # just return.
    else:
        return resp

    # loop the response to get entries for the 'directory'
    # type.
    for entry in response:
        file_name, file_type = entry

        if file_type == 'file':
            if ' ' in file_name:
                resp[f"'{file_name}'"] = file_name
            else:
                resp[file_name] = file_name

    return resp

def list_content_in_current_fm_directory() -> dict:
    """
        Return folders and files in the current working directory of the
        Frida attached device.
    """

    resp = {}

    # check for existence based on the runtime
    if device_state.platform == Ios:
        response = _get_short_ios_listing()

    elif device_state.platform == Android:
        response = _get_short_android_listing()

    # looks like we landed in an unknown runtime.
    # just return.
    else:
        return resp

    # loop the response to get entries.
    for entry in response:
        name, _ = entry

        if ' ' in name:
            resp[f"'{name}'"] = name
        else:
            resp[name] = name

    return resp
