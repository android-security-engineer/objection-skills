import click
from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json


def entries(args: list = None) -> None:
    """
        Lists entries in the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ks = api.android_keystore_list()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'entries': ks, 'count': len(ks)}),
            command='android keystore list',
        )

    output = [[x['alias'], x['is_key'], x['is_certificate']] for x in ks]
    click.secho(tabulate(output, headers=['Alias', 'Key', 'Certificate']))
    return None


def detail(args: list = None) -> None:
    """
        Lists details of all items in the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    ks = api.android_keystore_detail()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'details': ks, 'count': len(ks)}),
            command='android keystore detail',
        )

    click.secho('Listing details for all items in the Android KeyStore...', dim=True)
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

    click.secho(tabulate(output, headers=[
        'Alias', 'Alg', 'Size', 'Modes', 'Paddings', 'Digests',
        'Validity Start', 'Origin', 'Purposes', 'Sig Paddings', 'Sec Hardware'
    ]))
    return None


def clear(args: list = None) -> None:
    """
        Clears out an Android KeyStore

        :param args:
        :return:
    """

    # JSON 模式下跳过交互确认（Agent 无法回答 confirm）
    if not should_output_json(args):
        if not click.confirm('Are you sure you want to clear the Android keystore?'):
            return None

    api = state_connection.get_api()
    api.android_keystore_clear()

    if should_output_json(args):
        return output_result(
            CommandResult(result={'cleared': True}),
            command='android keystore clear',
        )
    return None


def watch(args: list = None) -> None:
    """
        Watches usage of the Android KeyStore

        :param args:
        :return:
    """

    api = state_connection.get_api()
    api.android_keystore_watch()

    if should_output_json(args):
        return output_result(
            CommandResult(
                result={'watching': True},
                warnings=['Job id not surfaced; use `agent state` to list running jobs.'],
            ),
            command='android keystore watch',
        )
    return None
