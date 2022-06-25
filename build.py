#!/usr/bin/env python
import os
from glob import glob
from pathlib import Path
from webbrowser import get
from config import *
from datetime import datetime
import copy_to_efi
import subprocess
import requests
import tqdm
import click

import apecid
import environment
from run import run

ENV = environment.get_env()
DEFAULT_VERSION = "0.8.1"

HACKINTOSH_ROOT = Path(ENV['HACKINTOSH_ROOT'])
UPDATED_DIR = Path(ENV['UPDATED_DIR'])
DOWNLOADS_DIR = Path(ENV['DOWNLOADS_DIR'])
USER_EFI_DIR = Path(ENV['USER_EFI_DIR'])
KEYS_DIR = Path(ENV['KEYS_DIR'])
USER_OPENCORE_DIR = Path(ENV['USER_OPENCORE_DIR'])
USER_OPENCORE_DRIVERS_DIR = Path(ENV['USER_OPENCORE_DRIVERS_DIR'])
SIGNED_DIR = Path(ENV['SIGNED_DIR'])
BOOT_VOLUME_NAME = ENV['BOOT_VOLUME_NAME']
BACKUP_VOLUME_NAME = ENV['BACKUP_VOLUME_NAME']

temp_directories = [DOWNLOADS_DIR, SIGNED_DIR, UPDATED_DIR]


def create_directories():
    for dir in temp_directories:
        if not dir.exists():
            click.echo('creating ' + dir)
            os.mkdir(dir)
    # make signed subdirs
    for dir in ["OC", "BOOT"]:
        os.mkdir(SIGNED_DIR / dir)


def print_diagnostics(version: str = DEFAULT_VERSION, release: str = "RELEASE", sign: bool = False, vault: bool = True, backup: bool = True, write: bool = False):
    click.echo(click.style('Diagnostics:', bold=True))
    click.echo('Boot volume name is ' + BOOT_VOLUME_NAME)
    click.echo('Backup volume name is ' + BACKUP_VOLUME_NAME)
    click.echo(f'Hackintosh root is {str(HACKINTOSH_ROOT)}')
    click.echo(click.style(f'OpenCore version: {version}', fg='green'))
    click.echo(click.style(f'release: {release}', fg='green'))
    sign_msg = 'Will sign for UEFI secure boot' if sign else click.style(
        'UEFI secure boot = OFF', fg='red')
    vault_msg = 'Will create Apple Secure Boot vault' if sign else click.style(
        'Skipping vault.', fg='red')
    backup_msg = 'Will backup current EFI to backup volume' if backup else click.style(
        'Skipping backup.', fg='red')
    write_msg = 'Will write to boot volume' if write else click.style(
        '', fg='red')
    for msg in [sign_msg, vault_msg, backup_msg, write_msg]:
        click.echo(msg)


def clean_dir(dir: str):
    for file in glob(f'{dir}/*'):
        os.remove(file)
    os.rmdir(f'{dir}')
    click.echo('removed ' + dir)


def cleanup():
    for path in temp_directories:
        clean_dir(path)


def get_user_drivers_list():
    return glob(USER_OPENCORE_DRIVERS_DIR / '*.efi')


def user_path_to_download_path(path: Path) -> Path:
    replaced = str(path).replace(str(USER_EFI_DIR),
                                 str(Path(DOWNLOADS_DIR + '/X64/EFI')))
    return Path(replaced)


def is_user_file_in_downloads(path: Path) -> bool:
    download_path = user_path_to_download_path(path)
    return download_path.exists()


def user_or_updated(path: Path):
    if is_user_file_in_downloads(path):
        name = path.name
        click.echo(click.style('Will use updated ' + name, fg='yellow'))
        output = user_path_to_download_path(path)
    else:
        output = path
    return output


def get_user_drivers_list_with_updates():
    user_drivers = get_user_drivers_list()
    return list(map(lambda driver: user_or_updated(driver), user_drivers))


def copy_user_files(update: bool = True):
    os.system('cp -r ' + USER_EFI_DIR + '/* ' + UPDATED_DIR)
    if not update:
        click.echo('copied current version of user files to signed directory')
    else:
        click.echo(
            'will update user files and copy to updated directory and then to signed directory')
        UPDATED_OC_DRIVERS_DIR = UPDATED_DIR / 'OC/Drivers'
        for file in glob(f'{UPDATED_OC_DRIVERS_DIR}/*.efi'):
            os.remove(file)
            click.echo('Removed ' + file)
        click.echo(
            'Finished purging all OpenCore drivers. Now inserting existing or updated if available')
        user_drivers = get_user_drivers_list_with_updates()
        for file in user_drivers:
            click.echo(
                f'copying {file} to {UPDATED_OC_DRIVERS_DIR}/{file.name}')
            os.system('cp ' + file + ' ' +
                      UPDATED_OC_DRIVERS_DIR + '/' + file.name)
        click.echo('Finished copying user files to updated directory')
        os.system('mv ' + USER_EFI_DIR + ' ' + 'EFI_TEMP')
        os.system('mv ' + UPDATED_DIR + ' ' + 'EFI')
        os.system('rm -rfv EFI_TEMP')
        click.echo('Finished cleaning up EFI_TEMP')


def validate_config(vault: bool):
    # run ocvalidate
    ocvalidate_path = Path(f'{DOWNLOADS_DIR}/Utilities/ocvalidate')
    config_path = get_config_path()
    valid = run([ocvalidate_path, config_path])
    if not valid:
        raise Exception(
            'ocvalidate returned a non-zero exit code. Please run ocvalidate manually for more information.')
    config_plist = parse_config_file(USER_OPENCORE_DIR)
    # check values for efi files
    drivers_list = list(map(lambda path: path.name), get_user_drivers_list())
    for driver in drivers_list:
        if driver not in config_plist['UEFI']['Drivers']:
            raise Exception('missing driver ' +
                            driver + ' in UEFI->Drivers')
    # check config_plist values for vault
    if vault:
        click.echo('Checking Apple Secure Boot configuration')
        if config_plist['Misc']['Security']['Vault'] != 'Secure':
            raise Exception('Misc->Security->Vault is not set to Secure')
        # check values for windows dual boot
        if config_plist['Booter']['Quirks']['DevirtualiseMmio'] != True:
            raise Exception(
                'Booter->Quirks->DevirtualiseMmio is not set to True')
        if config_plist['Booter']['Quirks']['ProtectUefiServices'] != True:
            raise Exception(
                'Booter->Quirks->ProtectUefiServices is not set to True')
        if config_plist['Booter']['Quirks']['SyncRuntimePermissions'] != True:
            raise Exception(
                'Booter->Quirks->SyncRuntimePermissions is not set to True')


def check_signed(files: list = []) -> bool:
    SIGNED_DIR = ENV['SIGNED_DIR']
    code = 0
    if not len(files):
        raise Exception('check_signed was called with an empty list of files')
    for file in files:
        code += run_multipass(
            f'sbverify --list {SIGNED_DIR}/{file}')
        if not code == 0:
            raise Exception(f'{file} is not signed')
    return code == 0


def make_vault(signed: bool = True):
    utilities = DOWNLOADS_DIR / 'Utilities/CreateVault'
    os.system('cp -Rv ' + utilities + ' ' + HACKINTOSH_ROOT + '/')
    if signed:
        os.system(f'mv {USER_EFI_DIR} {HACKINTOSH_ROOT}/EFI_TEMP')
        os.system(f'mv {SIGNED_DIR} {HACKINTOSH_ROOT}/EFI')
    utilities = Path(HACKINTOSH_ROOT / 'Utilities')
    if not utilities.exists():
        raise Exception('could not find Utilities directory')
    path = utilities / 'CreateVault' / 'sign.command'
    output = run([path])
    if signed:
        os.system(f'mv {USER_EFI_DIR} {SIGNED_DIR}')
        os.system(f'mv {HACKINTOSH_ROOT}/EFI_TEMP {USER_EFI_DIR}')
    os.system(f'rm -rf {utilities}')
    if output != 0:
        raise Exception('CreateVault returned a non-zero exit code')
    return output


def check_vault(signed: bool = True):
    dir = SIGNED_DIR if signed else USER_EFI_DIR
    files = ['vault.plist', 'vault.sig'].map(
        lambda x: Path(dir) / 'OC' / x)
    for file in files:
        if not file.exists():
            raise Exception('could not find ' + file)


def download(url: str, dest_dir: str = ENV['DOWNLOADS_DIR']):
    file_name = url.split("/")[-1]
    dest_path = Path(dest_dir) / file_name
    click.echo(click.style('Downloading ' + url +
               ' to ' + dest_path, fg='green'))
    if dest_path.exists():
        click.echo('cleaning up ' + dest_path + ' before downloading')
        os.remove(dest_path)
    response = requests.get(url, stream=True)
    with open(dest_path, 'wb') as f:
        for chunk in tqdm(response.iter_content(chunk_size=1024)):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    if not dest_path.exists():
        raise Exception('failed to download ' + url)


def download_dependencies(version: str = DEFAULT_VERSION, release: str = "RELEASE"):
    DOWNLOADS_DIR = Path(ENV['DOWNLOADS_DIR'])
    DOWNLOADED_EFI_DIR = DOWNLOADS_DIR / 'X64/EFI'
    DOWNLOADED_DRIVERS_DIR = DOWNLOADED_EFI_DIR / 'OC/Drivers'
    download(
        f'https://github.com/acidanthera/OpenCorePkg/releases/download/{version}/OpenCore-{version}-{release}.zip', ENV['DOWNLOADS_DIR'])
    # unzip opencore
    run(['unzip', '-o',
        f'{str(DOWNLOADS_DIR)}/OpenCore-{version}-{release}.zip', '-d', str(DOWNLOADS_DIR)])
    if not '{DOWNLOADS_DIR}/X64/EFI/OC/OpenCore.efi'.exists():
        raise Exception('could not find downloaded OpenCore.efi')
    else:
        click.echo('Successfully extracted OpenCore release')
    for file in glob(DOWNLOADS_DIR + '/*.zip'):
        click.echo('cleaning up ' + file)
        os.remove(file)
    download('https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/HfsPlus.efi',
             DOWNLOADED_DRIVERS_DIR)
    download('https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/ext4_x64.efi',
             DOWNLOADED_DRIVERS_DIR)


def check_keys():
    isk_files = ['key', 'pem'].map(lambda ext: KEYS_DIR / f'ISK.{ext}')
    for file in isk_files:
        if not file.exists():
            raise Exception('could not find ' + file)
        click.echo("Found " + file)
    pass


def bless_partition():
    click.echo('blessing partition')
    return run(['bless --folder "/System/Library/CoreServices" --bootefi --personalize'])


def mount_efi(name):
    cwd = os.getcwd()
    status = subprocess.run(
        [f'{cwd}/mountefi/MountEFI.command', name], check=True, env=ENV).returncode
    if status != 0:
        raise Exception('MountEFI returned a non-zero exit code')
    return status


def unmount_efi(name):
    cwd = os.getcwd()
    status = subprocess.run(
        [f'{cwd}/mountefi/MountEFI.command', '-u', name], check=True, env=ENV).returncode
    if status != 0:
        raise Exception(
            'MountEFI returned a non-zero exit code when attempting to unmount ' + name)
    return status


def date_filename():
    now = datetime.now()
    return now.strftime('%Y%m%dT%H%M%S')


@click.command()
@click.option('--version', default=DEFAULT_VERSION)
@click.option('--release', default="RELEASE")
@click.option('--sign', default=True)
@click.option('--vault', default=True)
@click.option('--backup', default=False)
@click.option('--write', default=False)
@click.option('--update', default=True)
def build(version: str = DEFAULT_VERSION, release: str = "RELEASE", sign: bool = False, vault: bool = True, backup: bool = False, write: bool = False, update: bool = True):
    print_diagnostics(version, release, sign, vault, backup, write)
    # validate config.plist
    # TODO: do apecid
    check_keys()
    # bless_partition()
    # download dependencies
    download_dependencies(version, release)
    validate_config(vault)
    # copy user files or updated files to updated dir
    copy_user_files(update)
    if sign:
        # sign opencore drivers for uefi secure boot
        to_sign = glob(USER_EFI_DIR + 'OC/Drivers/*.efi')
        sign.sign_all(to_sign, USER_EFI_DIR)

    # create vault
    make_vault()
    # sign OpenCore EFI and BOOTx64.efi
    sign.sign_opencore(USER_EFI_DIR)
    # TODO: (optional) create vault again?
    # mount efi
    if write or backup:
        mount_efi(BOOT_VOLUME_NAME)
        # backup current efi to file
        filename = Path(os.getcwd() + '/backups/' + date_filename())
        click.echo('Backing up current EFI to ' + filename)
        BACKUPS_DIR = os.getcwd() + '/backups'
        os.system(f'mkdir -p {BACKUPS_DIR}/{filename}')
        os.system(f'rm -rf {BACKUPS_DIR}/{filename}/*')
        os.system(f'cp -Rv /Volumes/EFI/EFI/* {BACKUPS_DIR}/{filename}')
        run(['7z a {BACKUPS_DIR}/{filename}/* {BACKUPS_DIR}/{filename}.7z'])
        click.echo('Backed up current efi to {BACKUPS_DIR}/{filename}.7z')
        unmount_efi(BOOT_VOLUME_NAME)
        if backup:
            click.echo('Cleaning up backup volume')
            mount_efi(BACKUP_VOLUME_NAME)
            os.system('rm -rf /Volumes/EFI/*')
            os.system('mkdir -p /Volumes/EFI/EFI')
            copy_to_efi.copy_to_efi('{BACKUPS_DIR}/{filename}', '/Volumes/EFI')
            click.echo('Copied to backup volume')
            unmount_efi(BACKUP_VOLUME_NAME)
        if write:
            mount_efi(BOOT_VOLUME_NAME)
            path_to_copy = SIGNED_DIR if sign else USER_EFI_DIR
            copy_to_efi.copy_to_efi(path_to_copy, '/Volumes/EFI')
            unmount_efi(BOOT_VOLUME_NAME)
    click.echo(click.style('Done!', fg='green', bold=True, blink=True))


if __name__ == '__main__':
    build()
