import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def entries(args: list = None) -> CommandResult:
    """
        Lists entries in the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ks = api.android_keystore_list()

    output = [[x['alias'], x['is_key'], x['is_certificate']] for x in ks]
    human_text = tabulate(output, headers=['Alias', 'Key', 'Certificate'])
    return output_result(
        CommandResult(result={'entries': ks, 'count': len(ks)}, human_text=human_text),
        command='android keystore list',
    )


def detail(args: list = None) -> CommandResult:
    """
        Lists details of all items in the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ks = api.android_keystore_detail()

    human_text = 'Listing details for all items in the Android KeyStore...\n'
    output = [[
        x['keystoreAlias'],
        x['keyAlgorithm'],
        x['keySize'],
        ','.join(x['blockModes']),
        ','.join(x['encryptionPaddings']),
        ','.join(x['digests']),
        x['keyValidityStart'],
        x['origin'],
        x['purposes'],
        ','.join(x['signaturePaddings']),
        x['isInsideSecureHardware'],
    ] for x in ks]

    human_text += tabulate(output, headers=[
        'Alias', 'Alg', 'Size', 'Modes', 'Paddings', 'Digests',
        'Validity Start', 'Origin', 'Purposes', 'Sig Paddings', 'Sec Hardware'
    ])
    return output_result(
        CommandResult(result={'details': ks, 'count': len(ks)}, human_text=human_text),
        command='android keystore detail',
    )


def clear(args: list = None) -> CommandResult:
    """
        Clears out an Android KeyStore

        :param args:
        :return:
    """

    # Agent / JSON 模式下跳过交互确认，直接执行
    if not should_output_json(args):
        if not click.confirm('Are you sure you want to clear the Android keystore?'):
            human_text = 'Keystore clear cancelled'
            return output_result(
                CommandResult(result={'cleared': False}, human_text=human_text),
                command='android keystore clear',
            )

    api = state_connection.get_api()
    api.android_keystore_clear()

    human_text = 'Android keystore cleared'
    return output_result(
        CommandResult(result={'cleared': True}, human_text=human_text),
        command='android keystore clear',
    )


def watch(args: list = None) -> CommandResult:
    """
        Watches usage of the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_keystore_watch()

    return output_result(
        CommandResult(
            result={'watching': True},
            human_text='Watching Android keystore',
            warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
        ),
        command='android keystore watch',
    )
