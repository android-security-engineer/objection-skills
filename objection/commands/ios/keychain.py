import json
from typing import Optional

import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def _should_do_smart_decode(args: list) -> bool:
    """
        Checks if --smart is in the list of tokens received from the
        command line.

        :param args:
        :return:
    """

    return len(args) > 0 and '--smart' in args


def _data_flag_has_identifier(args: list) -> bool:
    """
        Checks that if the data flag is specified, an identifier
        is also passed.

        :param args:
        :return:
    """

    if '--data' in args:
        return any(x in args for x in ['--service', '--account'])

    return True


def _get_flag_value(args: list, flag: str) -> Optional[str]:
    """
        Returns the value for a flag.

        :param args:
        :param flag:
        :return:
    """

    return args[args.index(flag) + 1] if flag in args else None


def _get_json_destination(args: list) -> Optional[str]:
    """
        返回 --json 标志跟随的文件名（若有）。
    """

    if not args or '--json' not in args:
        return None
    idx = args.index('--json')
    if idx + 1 < len(args):
        return args[idx + 1]
    return None


def dump(args: list = None) -> Optional[CommandResult]:
    """
        Dump the iOS keychain

        :param args:
        :return:
    """

    api = state_connection.get_api()
    keychain = api.ios_keychain_list(_should_do_smart_decode(args))

    destination = _get_json_destination(args)

    # --json <filename> 保留旧行为：写文件
    if destination:
        with open(destination, 'w') as f:
            f.write(json.dumps(keychain, indent=2))
        return output_result(
            CommandResult(
                result={'dumped_to': destination, 'count': len(keychain)},
                human_text='Writing keychain as json to {0}...'.format(destination),
            ),
            command='ios keychain dump',
        )

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'entries': keychain, 'count': len(keychain), 'smart_decoded': _should_do_smart_decode(args)},
            ),
            command='ios keychain dump',
        )

    human_lines = tabulate(
        [[
            entry.get('create_date'),
            entry.get('accessible_attribute', '').replace('kSecAttrAccessible', '') if 'accessible_attribute' in entry else None,
            entry.get('access_control'),
            entry.get('item_class', '').replace('kSecClassGeneric', ''),
            entry.get('account'),
            entry.get('service'),
            entry.get('data'),
        ] for entry in keychain], headers=['Created', 'Accessible', 'ACL', 'Type', 'Account', 'Service', 'Data'],
    )
    return output_result(
        CommandResult(
            result={'entries': keychain, 'count': len(keychain), 'smart_decoded': _should_do_smart_decode(args)},
            human_text=human_lines,
        ),
        command='ios keychain dump',
    )


def dump_raw(args: list = None) -> Optional[CommandResult]:
    """
        Dump the iOS keychain, but without any parsing.
        The agent will output the entries it finds here.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.ios_keychain_list_raw()

    return output_result(
        CommandResult(
            result={'action': 'dumped_raw'},
            human_text='Dumping the iOS keychain...',
            warnings=['Raw entries are emitted by the agent as async messages; poll via `agent state` or HTTP /events.'],
        ),
        command='ios keychain dump_raw',
    )


def clear(args: list = None) -> Optional[CommandResult]:
    """
        Clear the iOS keychain.

        :param args:
        :return:
    """

    # JSON 模式下跳过交互确认（Agent 无法回答 confirm）
    if should_output_json(args):
        api = state_connection.get_api()
        api.ios_keychain_empty()
        return output_result(
            CommandResult(result={'cleared': True}, human_text='Keychain cleared'),
            command='ios keychain clear',
        )

    if not click.confirm('Are you sure you want to clear the iOS keychain?'):
        return None

    click.secho('Clearing the keychain...', dim=True)

    api = state_connection.get_api()
    api.ios_keychain_empty()

    click.secho('Keychain cleared', fg='green')
    return None


def remove(args: list) -> Optional[CommandResult]:
    """
        Remove matching keychain entries from the keychain

        :param args:
        :return:
    """

    account = _get_flag_value(args, '--account')
    service = _get_flag_value(args, '--service')

    if not account or not service:
        return output_result(
            CommandResult(
                result={'error': 'either --account or --service is not set; both are required'},
                status='error',
                human_text='Either --account or --service is not set. We need both',
                exit_code=1,
            ),
            command='ios keychain remove',
        )

    api = state_connection.get_api()
    api.ios_keychain_remove(account, service)

    return output_result(
        CommandResult(
            result={'removed': True, 'account': account, 'service': service},
            human_text='Successfully removed matching keychain items',
        ),
        command='ios keychain remove',
    )


def update(args: list) -> Optional[CommandResult]:
    """
        Update matching keychain entry from the keychain

        :param args:
        :return:
    """

    account = _get_flag_value(args, '--account')
    service = _get_flag_value(args, '--service')
    newdata = _get_flag_value(args, '--newdata')

    if not account or not service or not newdata:
        return output_result(
            CommandResult(
                result={'error': 'all flags required: --account, --service, --newdata'},
                status='error',
                human_text='All flags need to be set, incl. --account, --service and --newdata',
                exit_code=1,
            ),
            command='ios keychain update',
        )

    api = state_connection.get_api()
    api.ios_keychain_update(account, service, newdata)

    return output_result(
        CommandResult(
            result={'updated': True, 'account': account, 'service': service},
            human_text='Successfully updated matching keychain item',
        ),
        command='ios keychain update',
    )


def add(args: list) -> Optional[CommandResult]:
    """
        Adds a new kSecClassGenericPassword keychain entry to the keychain

        :param args:
        :return:
    """

    if not _data_flag_has_identifier(args):
        return output_result(
            CommandResult(
                result={'error': 'when --data is specified, --account or --service is also required'},
                status='error',
                human_text='When specifying the --data flag, either --account or '
                            '--service should also be added',
                exit_code=1,
            ),
            command='ios keychain add',
        )

    account = _get_flag_value(args, '--account')
    service = _get_flag_value(args, '--service')
    data = _get_flag_value(args, '--data')

    api = state_connection.get_api()
    success = api.ios_keychain_add(account, service, data)

    return output_result(
        CommandResult(
            result={'added': bool(success), 'account': account, 'service': service},
            status='ok' if success else 'error',
            exit_code=0 if success else 1,
            human_text='Successfully added the keychain item' if success else 'Failed to add the keychain item',
        ),
        command='ios keychain add',
    )
