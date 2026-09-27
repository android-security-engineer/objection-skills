import os
import shutil
from typing import Optional

import click
import delegator
from packaging.version import Version

from objection.utils.output import CommandResult, output_result
from ..utils.patchers.android import AndroidGadget, AndroidPatcher
from ..utils.patchers.github import Github
from ..utils.patchers.ios import IosGadget, IosPatcher


def _should_output_json(args: list = None) -> bool:
    """
        Check if we should output JSON instead of human-readable text.
        For mobile_packages, this is always False since these are build operations,
        not agent commands. But we keep the check for consistency.
    """
    return False


def patch_ios_ipa(source: str, codesign_signature: str, provision_file: str, binary_name: str,
                  skip_cleanup: bool, unzip_unicode: bool, gadget_version: str = None,
                  pause: bool = False, gadget_config: str = None, script_source: str = None,
                  bundle_id: str = None) -> CommandResult:
    """
        Patches an iOS IPA by extracting, injecting the Frida dylib,
        codesigning the dylib and app executable and rezipping the IPA.

        :param bundle_id:
        :param source:
        :param codesign_signature:
        :param provision_file:
        :param binary_name:
        :param skip_cleanup:
        :param unzip_unicode:
        :param gadget_version:
        :param pause:
        :param gadget_config:
        :param script_source:
        :return:
    """

    messages = []

    github = Github(gadget_version=gadget_version)
    ios_gadget = IosGadget(github)

    # get the gadget version numbers
    # check if a gadget version was specified. if not, get the latest one.
    if gadget_version is not None:
        github_version = gadget_version
        messages.append('Using manually specified version: {0}'.format(gadget_version))
    else:
        github_version = github.get_latest_version()
        messages.append('Using latest Github gadget version: {0}'.format(github_version))

    # get the local version number of the stored gadget
    local_version = ios_gadget.get_local_version('ios_universal')

    # check if the local version needs updating. this can be either because
    # the version is outdated or we simply don't have the gadget yet
    if Version(github_version) != Version(local_version) or not ios_gadget.gadget_exists():
        # download!
        messages.append('Remote FridaGadget version is v{0}, local is v{1}. Downloading...'.format(
            github_version, local_version))

        # download, unpack, update local version and cleanup the temp files.
        ios_gadget.download() \
            .unpack() \
            .set_local_version('ios_universal', github_version) \
            .cleanup()

    messages.append('Patcher will be using Gadget version: {0}'.format(github_version))

    # start the patching process
    patcher = IosPatcher(skip_cleanup=skip_cleanup)

    # return of we do not have all of the requirements.
    if not patcher.are_requirements_met():
        return output_result(
            CommandResult(result={'error': 'requirements not met'},
                          status='error',
                          human_text='Requirements not met for patching'),
            command='patch ios',
        )

    patcher.set_provsioning_profile(provision_file=provision_file, bundle_id=bundle_id)
    patcher.extract_ipa(unzip_unicode, ipa_source=source)
    patcher.set_application_binary(binary=binary_name)
    patcher.patch_and_codesign_binary(
        frida_gadget=ios_gadget.get_gadget_path(), codesign_signature=codesign_signature, gadget_config=gadget_config)

    if script_source:
        messages.append('Copying over a custom script to use with the gadget config.')
        shutil.copyfile(script_source, os.path.join(patcher.app_folder, 'Frameworks', script_source))

    # give a chance to make any last minute modifications if needed
    if pause:
        messages.append('Patching paused. The next step is to rebuild the IPA. '
                        'If you require any manual fixes, the current temp directory is:')
        messages.append(patcher.app_folder)
        # in agent/json mode we cannot interact; just record the pause state
        if _should_output_json(None):
            messages.append('Pause skipped in non-interactive mode.')

    patcher.archive_and_codesign(original_name=source, codesign_signature=codesign_signature)

    messages.append('Copying final ipa from {0} to current directory...'.format(patcher.get_patched_ipa_path()))
    shutil.copyfile(
        patcher.get_patched_ipa_path(),
        os.path.join(os.path.abspath('.'), os.path.basename(patcher.get_patched_ipa_path())))

    return output_result(
        CommandResult(result={'action': 'patched_ios', 'output': patcher.get_patched_ipa_path()},
                      human_text='\n'.join(messages)),
        command='patch ios',
    )


def patch_android_apk(source: str, architecture: str, pause: bool, skip_cleanup: bool = True,
                      enable_debug: bool = True, gadget_version: str = None, skip_resources: bool = False,
                      network_security_config: bool = False, target_class: str = None,
                      use_aapt2: bool = False, gadget_config: str = None, script_source: str = None,
                      ignore_nativelibs: bool = True, manifest: str = None, skip_signing: bool = False,
                      only_main_classes: bool = False, fix_concurrency_to = None) -> CommandResult:
    """
        Patches an Android APK by extracting, patching SMALI, repackaging
        and signing a new APK.

        :param source:
        :param architecture:
        :param pause:
        :param skip_cleanup:
        :param enable_debug:
        :param gadget_version:
        :param skip_resources:
        :param network_security_config:
        :param target_class:
        :param use_aapt2:
        :param gadget_config:
        :param script_source:
        :param ignore_nativelibs:
        :param only_main_classes:
        :param fix_concurrency_to:

        :return:
    """

    messages = []

    github = Github(gadget_version=gadget_version)
    android_gadget = AndroidGadget(github)

    # without an architecture set, attempt to determine one using adb
    if not architecture:
        messages.append('No architecture specified. Determining it using `adb`...')
        o = delegator.run('adb shell getprop ro.product.cpu.abi')

        # read the ach from the process' output
        architecture = o.out.strip()

        if len(architecture) <= 0:
            messages.append('Failed to determine architecture. Is the device connected and authorized?')
            return output_result(
                CommandResult(
                    result={'error': 'failed to determine architecture'},
                    status='error',
                    human_text='\n'.join(messages),
                    exit_code=1,
                ),
                command='patch android',
            )

        messages.append('Detected target device architecture as: {0}'.format(architecture))

    # set the architecture we are interested in
    android_gadget.set_architecture(architecture)

    # check the gadget config flags
    if script_source and not gadget_config:
        messages.append('A script source was specified but no gadget configuration was set.')
        return output_result(
            CommandResult(
                result={'error': 'gadget_config required when script_source is set'},
                status='error',
                human_text='\n'.join(messages),
                exit_code=1,
            ),
            command='patch android',
        )

    # check if a gadget version was specified. if not, get the latest one.
    if gadget_version is not None:
        github_version = gadget_version
        messages.append('Using manually specified version: {0}'.format(gadget_version))
    else:
        github_version = github.get_latest_version()
        messages.append('Using latest Github gadget version: {0}'.format(github_version))

    # get local version of the stored gadget
    local_version = android_gadget.get_local_version('android_' + architecture)

    # check if the local version needs updating. this can be either because
    # the version is outdated or we simply don't have the gadget yet, or, we want
    # a very specific version
    if Version(github_version) != Version(local_version) or not android_gadget.gadget_exists():
        # download!
        messages.append('Remote FridaGadget version is v{0}, local is v{1}. Downloading...'.format(
            github_version, local_version))

        # download, unpack, update local version and cleanup the temp files.
        android_gadget.download() \
            .unpack() \
            .set_local_version('android_' + architecture, github_version) \
            .cleanup()

    messages.append('Patcher will be using Gadget version: {0}'.format(github_version))

    patcher = AndroidPatcher(skip_cleanup=skip_cleanup, skip_resources=skip_resources, manifest=manifest, only_main_classes=only_main_classes)

    # ensure that we have all of the commandline requirements
    if not patcher.are_requirements_met():
        messages.append('Requirements not met for patching')
        return output_result(
            CommandResult(
                result={'error': 'requirements not met'},
                status='error',
                human_text='\n'.join(messages),
                exit_code=1,
            ),
            command='patch android',
        )

    # ensure we have the latest apk-tool and run the
    if not patcher.is_apktool_ready():
        messages.append('apktool is not ready for use')
        return output_result(
            CommandResult(
                result={'error': 'apktool not ready'},
                status='error',
                human_text='\n'.join(messages),
                exit_code=1,
            ),
            command='patch android',
        )

    # work on patching the APK
    patcher.set_apk_source(source=source)
    patcher.unpack_apk(fix_concurrency_to=fix_concurrency_to)
    patcher.inject_internet_permission()

    if not ignore_nativelibs:
        patcher.extract_native_libs_patch()

    if enable_debug:
        patcher.flip_debug_flag_to_true()

    if network_security_config:
        patcher.add_network_security_config()

    patcher.inject_load_library(target_class=target_class)
    patcher.add_gadget_to_apk(architecture, android_gadget.get_frida_library_path(), gadget_config)

    if script_source:
        messages.append('Copying over a custom script to use with the gadget config.')
        shutil.copyfile(script_source,
                        os.path.join(patcher.apk_temp_directory, 'lib', architecture,
                                     'libfrida-gadget.script.so'))

    # if we are required to pause, do that.
    if pause:
        messages.append(('Patching paused. The next step is to rebuild the APK. '
                         'If you require any manual fixes, the current temp '
                         'directory is:'))
        messages.append(patcher.get_temp_working_directory())
        # in agent/json mode we cannot interact; just record the pause state
        if _should_output_json():
            messages.append('Pause skipped in non-interactive mode.')

    patcher.build_new_apk(use_aapt2=use_aapt2, fix_concurrency_to=fix_concurrency_to)
    patcher.zipalign_apk()
    if not skip_signing:
        patcher.sign_apk()

    # woohoo, get the APK!
    destination = source.replace('.apk', '.objection.apk')

    messages.append('Copying final apk from {0} to {1} in current directory...'.format(patcher.get_patched_apk_path(), destination))
    shutil.copyfile(patcher.get_patched_apk_path(), os.path.join(os.path.abspath('.'), destination))

    return output_result(
        CommandResult(
            result={'action': 'patched_android', 'output': destination},
            human_text='\n'.join(messages),
        ),
        command='patch android',
    )


def sign_android_apk(source: str, skip_cleanup: bool = True) -> CommandResult:
    """
        Zipaligns and signs an Android APK with the objection key.

        :param source:
        :param skip_cleanup:

        :return:
    """

    messages = []
    patcher = AndroidPatcher(skip_cleanup=skip_cleanup)

    # ensure that we have all of the commandline requirements
    if not patcher.are_requirements_met():
        messages.append('Requirements not met for signing')
        return output_result(
            CommandResult(
                result={'error': 'requirements not met'},
                status='error',
                human_text='\n'.join(messages),
                exit_code=1,
            ),
            command='sign android',
        )

    patcher.set_apk_source(source=source)
    patcher.zipalign_apk()
    patcher.sign_apk()

    # woohoo, get the APK!
    destination = source.replace('.apk', '.objection.apk')

    messages.append('Copying final apk from {0} to {1} in current directory...'.format(patcher.get_patched_apk_path(), destination))
    shutil.copyfile(patcher.get_patched_apk_path(), os.path.join(os.path.abspath('.'), destination))

    return output_result(
        CommandResult(
            result={'action': 'signed_android', 'output': destination},
            human_text='\n'.join(messages),
        ),
        command='sign android',
    )
