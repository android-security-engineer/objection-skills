import json
import os
from typing import List, Optional

from tabulate import tabulate

from objection.state.connection import state_connection
from objection.utils.output import CommandResult, output_result, should_output_json
from ..utils.helpers import clean_argument_flags
from ..utils.helpers import sizeof_fmt, pretty_concat

BLOCK_SIZE = 40960000


def _is_string_input(args: list) -> bool:
    """
        Checks if --string is in the list of tokens received form the
        command line.

        :param args:
        :return:
    """

    return len(args) > 0 and '--string' in args


def _should_only_dump_offsets(args: list) -> bool:
    """
        Checks if --offsets-only is in the list pf tokens received
        from the command line.

        :param args:
        :return:
    """

    return '--offsets-only' in args


def _is_string_pattern(args: list) -> bool:
    """
        Checks if --string-pattern is in the list of tokens received form the
        command line.

        :param args:
        :return:
    """

    return len(args) > 0 and '--string-pattern' in args


def _is_string_replace(args: list) -> bool:
    """
        Checks if --string-replace is in the list of tokens received form the
        command line.

        :param args:
        :return:
    """

    return len(args) > 0 and '--string-replace' in args


def _get_json_destination(args: list) -> Optional[str]:
    """
        返回 --json 标志跟随的文件名（若有）。
        用于区分「写文件」与「全局 JSON 模式走 stdout」。
    """

    if not args:
        return None
    try:
        idx = args.index('--json')
    except ValueError:
        return None
    if idx + 1 < len(args):
        return args[idx + 1]
    return None


def _get_chunks(addr: int, size: int, block_size: int = BLOCK_SIZE) -> List:
    """
        Determine chunks of

        :param addr:
        :param size:
        :param block_size:
        :return:
    """

    if size < block_size:
        return [(addr, size)]

    block_count = size // block_size
    extra_block = size % block_size
    current_address = addr
    ranges = []

    for i in range(block_count):
        ranges.append((current_address, block_size))
        current_address += block_size

    if extra_block != 0:
        ranges.append((current_address, extra_block))

    return ranges


# TODO: Dump memory on hooked methods.
# A PR in the repo this method is based on has an idea for this
#
# https://github.com/Nightbringer21/fridump/pull/3

def dump_all(args: list) -> CommandResult:
    """
        Dump memory from the currently injected process.
        Loosely based on:
            https://github.com/Nightbringer21/fridump

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing destination'},
                status='error',
                human_text='Usage: memory dump all <local destination>',
                exit_code=1,
            ),
            command='memory dump all',
        )

    # the destination file to write the dump to
    destination = args[0]

    # Check for file override
    if os.path.exists(destination):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'aborted', 'destination': destination},
                    status='error',
                    human_text='Destination file {dest} already exists'.format(dest=destination),
                    exit_code=1,
                ),
                command='memory dump all',
            )

        # human mode only
        if not click.confirm('Continue, appending to the file?'):
            return output_result(
                CommandResult(
                    result={'error': 'aborted', 'destination': destination},
                    status='error',
                    human_text='Destination file {dest} already exists'.format(dest=destination),
                    exit_code=1,
                ),
                command='memory dump all',
            )

    # access type used when enumerating ranges
    access = 'rw-'

    api = state_connection.get_api()
    ranges = api.memory_list_ranges(access)

    total_size = sum([x['size'] for x in ranges])
    human_text = 'Will dump {0} {1} images, totalling {2}\n\n'.format(
        len(ranges), access, sizeof_fmt(total_size))

    dumped_ranges = 0
    for image in ranges:
        dump = bytearray()

        # catch and exception thrown while dumping.
        # this could for a few reasons like if the protection
        # changes or the range is reallocated
        try:
            # grab the (size) bytes starting at the (base_address) in chunks of BLOCK_SIZE
            chunks = _get_chunks(int(image['base'], 16), int(image['size']), BLOCK_SIZE)
            for chunk in chunks:
                dump.extend(bytearray(api.memory_dump(chunk[0], chunk[1])))

        except Exception:
            continue

        dumped_ranges += 1
        # append the results to the destination file
        with open(destination, 'ab') as f:
            f.write(dump)

    human_text += 'Memory dumped to file: {0}'.format(destination)

    return output_result(
        CommandResult(
            result={
                'dumped_to': destination,
                'ranges_total': len(ranges),
                'ranges_dumped': dumped_ranges,
                'total_size': total_size,
            },
            human_text=human_text,
        ),
        command='memory dump all',
    )


def dump_from_base(args: list) -> CommandResult:
    """
        Dump memory from a base address for a specific size to file

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 3:
        return output_result(
            CommandResult(
                result={'error': 'missing arguments'},
                status='error',
                human_text='Usage: memory dump from_base <base_address> <size_to_dump> <local_destination>',
                exit_code=1,
            ),
            command='memory dump from_base',
        )

    # the destination file to write the dump to
    base_address = args[0]
    memory_size = args[1]
    destination = args[2]

    # Check for file override
    if os.path.exists(destination):
        if should_output_json(args):
            return output_result(
                CommandResult(
                    result={'error': 'aborted', 'destination': destination},
                    status='error',
                    human_text='Destination file {dest} already exists'.format(dest=destination),
                    exit_code=1,
                ),
                command='memory dump from_base',
            )

        if not click.confirm('Override?'):
            return output_result(
                CommandResult(
                    result={'error': 'aborted', 'destination': destination},
                    status='error',
                    human_text='Destination file {dest} already exists'.format(dest=destination),
                    exit_code=1,
                ),
                command='memory dump from_base',
            )

    human_text = 'Dumping {0} from {1} to {2}\n'.format(sizeof_fmt(int(memory_size)), base_address, destination)

    api = state_connection.get_api()

    # iirc, if you don't cast the return type to a bytearray it uses the sizeof(int) per cell, which is massive
    dump = bytearray()
    chunks = _get_chunks(int(base_address, 16), int(memory_size), BLOCK_SIZE)
    for chunk in chunks:
        dump.extend(bytearray(api.memory_dump(chunk[0], chunk[1])))

    # append the results to the destination file
    with open(destination, 'wb') as f:
        f.write(dump)

    human_text += 'Memory dumped to file: {0}'.format(destination)

    return output_result(
        CommandResult(
            result={
                'dumped_to': destination,
                'base': base_address,
                'size': int(memory_size),
                'bytes_written': len(dump),
            },
            human_text=human_text,
        ),
        command='memory dump from_base',
    )


def list_modules(args: list = None) -> CommandResult:
    """
        List modules loaded in the current process.

        :param args:
        :return:
    """

    api = state_connection.get_api()
    modules = api.memory_list_modules()

    destination = _get_json_destination(args)

    # --json <filename> 保留旧行为：写文件
    if destination:
        with open(destination, 'w') as f:
            f.write(json.dumps(modules, indent=2))
        return output_result(
            CommandResult(result={'dumped_to': destination, 'count': len(modules)},
                          human_text='Writing modules as json to {0}...'.format(destination)),
            command='memory list modules',
        )

    human_text = tabulate(
        [[
            entry['name'],
            entry['base'],
            str(entry['size']) + ' (' + sizeof_fmt(entry['size']) + ')',
            pretty_concat(entry['path']),
        ] for entry in modules], headers=['Name', 'Base', 'Size', 'Path'],
    )
    human_text += '\nSave the output by adding `--json modules.json` to this command'
    return output_result(
        CommandResult(result={'modules': modules, 'count': len(modules)}, human_text=human_text),
        command='memory list modules',
    )


def list_exports(args: list) -> CommandResult:
    """
        Dumps the exported methods from a loaded module to screen.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing module name'},
                status='error',
                human_text='Usage: memory list exports <module name>',
                exit_code=1,
            ),
            command='memory list exports',
        )

    module_to_list = args[0]

    api = state_connection.get_api()
    exports = api.memory_list_exports(module_to_list)

    destination = _get_json_destination(args)

    if destination:
        with open(destination, 'w') as f:
            f.write(json.dumps(exports, indent=2))
        return output_result(
            CommandResult(result={'dumped_to': destination, 'module': module_to_list, 'count': len(exports)},
                          human_text='Writing exports as json to {0}...'.format(destination)),
            command='memory list exports',
        )

    human_text = tabulate(
        [[
            entry['type'],
            entry['name'],
            entry['address'],
        ] for entry in exports], headers=['Type', 'Name', 'Address'],
    )
    return output_result(
        CommandResult(result={'module': module_to_list, 'exports': exports, 'count': len(exports)},
                      human_text=human_text),
        command='memory list exports',
    )


def find_pattern(args: list) -> CommandResult:
    """
        Searches the current processes accessible memory for a specific pattern.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) <= 0:
        return output_result(
            CommandResult(
                result={'error': 'missing pattern'},
                status='error',
                human_text='Usage: memory search "<pattern eg: 41 41 41 ?? 41>" (--string) (--offsets-only)',
                exit_code=1,
            ),
            command='memory search',
        )

    # if we got a string as input, convert it to hex
    if _is_string_input(args):
        pattern = ' '.join(hex(ord(x))[2:] for x in args[0])
    else:
        pattern = args[0]

    human_text = 'Searching for: {0}\n'.format(pattern)

    api = state_connection.get_api()
    data = api.memory_search(pattern, _should_only_dump_offsets(args))

    if len(data) > 0:
        human_text += 'Pattern matched at {0} addresses'.format(len(data))
        if _should_only_dump_offsets(args):
            human_text += '\n' + '\n'.join(data)
    else:
        human_text += 'Unable to find the pattern in any memory region'

    return output_result(
        CommandResult(result={'pattern': pattern, 'matches': data, 'count': len(data)},
                      human_text=human_text),
        command='memory search',
    )


def replace_pattern(args: list) -> CommandResult:
    """
        Searches the current processes accessible memory for a specific pattern and replaces it with given bytes or string.

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 2:
        return output_result(
            CommandResult(
                result={'error': 'missing arguments'},
                status='error',
                human_text=('Usage: memory replace "<search pattern eg: 41 41 ?? 41>" '
                            '"<replace value eg: 41 50>" (--string-pattern) (--string-replace)'),
                exit_code=1,
            ),
            command='memory replace',
        )

    # if we got a string as search pattern input, convert it to hex
    if _is_string_pattern(args):
        pattern = ' '.join(hex(ord(x))[2:] for x in args[0])
    else:
        pattern = args[0]

    # if we got a string as replace input, convert it to int[], otherwise convert hex to int[]
    replace = args[1]
    if _is_string_replace(args):
        replace = [ord(x) for x in replace]
    else:
        replace = [int(x, 16) for x in replace.split(' ')]

    api = state_connection.get_api()
    data = api.memory_replace(pattern, replace)

    human_text = 'Searching for: {0}, replacing with: {1}\n'.format(pattern, args[1])
    if len(data) > 0:
        human_text += 'Pattern replaced at {0} addresses'.format(len(data))
        if len(data) > 0:
            human_text += '\n' + '\n'.join(data)
    else:
        human_text += 'Unable to find the pattern in any memory region'

    return output_result(
        CommandResult(result={'pattern': pattern, 'replaced_at': data, 'count': len(data)},
                      human_text=human_text,
                      warnings=['In-memory replacement can be unstable; re-mapping or relinking may revert changes.']),
        command='memory replace',
    )


def write(args: list) -> CommandResult:
    """
        Write an arbitrary amount of bytes to an arbitrary memory address.

        Needless to say, use with caution. =P

        :param args:
        :return:
    """

    if len(clean_argument_flags(args)) < 2:
        return output_result(
            CommandResult(
                result={'error': 'missing arguments'},
                status='error',
                human_text='Usage: memory write "<address>" "<pattern eg: 41 41 41 41>" (--string)',
                exit_code=1,
            ),
            command='memory write',
        )

    destination = args[0]
    pattern = args[1]

    if _is_string_input(args):
        pattern = [ord(x) for x in pattern]
    else:
        pattern = [int(x, 16) for x in pattern.split(' ')]

    api = state_connection.get_api()
    api.memory_write(destination, pattern)

    return output_result(
        CommandResult(
            result={'action': 'wrote', 'address': destination, 'bytes': len(pattern)},
            human_text='Writing byte array: {0} to {1}'.format(pattern, destination),
            warnings=['Direct memory writes are dangerous and may crash the target.'],
        ),
        command='memory write',
    )
