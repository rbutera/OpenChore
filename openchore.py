#!/usr/bin/env python
import os
import subprocess
from datetime import datetime
from glob import glob
from pathlib import Path
from pprint import pprint

import click
import requests

from lib import apecid, config, copy_to_efi, environment
from lib import run as runlib
from lib import sign as signlib

multipass = runlib.multipass
run = runlib.run

ENV = environment.get_env()
VERSION = "0.8.1"

LOCAL_EFI_REPOSITORY = Path(ENV["LOCAL_EFI_REPOSITORY"])
UPDATED_DIR = Path(ENV["UPDATED_DIR"])
DOWNLOADS_DIR = Path(ENV["DOWNLOADS_DIR"])
USER_EFI_DIR = Path(ENV["USER_EFI_DIR"])
KEYS_DIR = Path(ENV["KEYS_DIR"])
USER_OPENCORE_DIR = Path(ENV["USER_OPENCORE_DIR"])
USER_OPENCORE_DRIVERS_DIR = Path(ENV["USER_OPENCORE_DRIVERS_DIR"])
SIGNED_DIR = Path(ENV["SIGNED_DIR"])
BOOT_VOLUME_NAME = ENV["BOOT_VOLUME_NAME"]
BACKUP_VOLUME_NAME = ENV["BACKUP_VOLUME_NAME"]
BACKUPS_DIR = Path(os.getcwd() + "/backups")
BACKUP_DATE = datetime.now().strftime("%Y%m%dT%H%M%S")
BACKUP_DIR = Path(ENV["BACKUP_DIR"])
BACKUP_DESTINATION = Path(f"{BACKUP_DIR}/{BACKUP_DATE}")


temp_directories = [DOWNLOADS_DIR, SIGNED_DIR, UPDATED_DIR]


def create_directories():
    cleanup()
    for dir in temp_directories:
        os.system("rm -rf " + str(dir))
        click.echo("creating " + str(dir))
        os.mkdir(dir)
    # make signed subdirs
    for dir in ["OC", "BOOT"]:
        os.mkdir(SIGNED_DIR / dir)


def print_diagnostics(
    version: str = VERSION,
    release: str = "RELEASE",
    sign: bool = False,
    vault: bool = True,
    backup: bool = True,
    write: bool = False,
):
    click.echo(click.style("Diagnostics:", bold=True))
    click.echo("Boot volume name is " + BOOT_VOLUME_NAME)
    click.echo("Backup volume name is " + BACKUP_VOLUME_NAME)
    click.echo(f"Hackintosh root is {str(LOCAL_EFI_REPOSITORY)}")
    click.echo(click.style(f"OpenCore version: {version}", fg="green"))
    click.echo(click.style(f"release: {release}", fg="green"))
    sign_msg = (
        "Will sign for UEFI secure boot"
        if sign
        else click.style("UEFI secure boot = OFF", fg="red")
    )
    vault_msg = (
        "Will create Apple Secure Boot vault"
        if sign
        else click.style("Skipping vault.", fg="red")
    )
    backup_msg = (
        "Will backup current EFI to backup volume"
        if backup
        else click.style("Skipping backup.", fg="red")
    )
    write_msg = "Will write to boot volume" if write else click.style(
        "", fg="red")
    for msg in [sign_msg, vault_msg, backup_msg, write_msg]:
        click.echo(msg)


def clean_dir(dir: str):
    to_remove = glob(f'{dir}/**/*.*')
    num_files = len(to_remove)
    if num_files > 0:
        click.echo(
            click.style(
                f'WARNING: there are {num_files} files in {dir} that will be removed!',
                fg='yellow',
                bold=True
            )
        )
    for file in to_remove:
        path = Path(file)
        click.echo(f'removing {file}')
        os.system(f'rm -rf {path}')
    os.system(f"rm -rf {dir}")
    click.echo(f"removed {dir}")


def cleanup():
    temp_paths_to_clean = [x for x in temp_directories if x != SIGNED_DIR]
    for path in temp_paths_to_clean:
        clean_dir(path)
    os.system(f"rm -rf {BACKUP_DIR}/")
    click.echo(click.style("Cleaned up temp directories", fg="green"))


def get_user_drivers_list():
    return glob(f"{USER_OPENCORE_DRIVERS_DIR}/*.efi")


def user_path_to_download_path(path: Path) -> Path:
    replaced = str(path).replace(
        str(USER_EFI_DIR), str(Path(f"{DOWNLOADS_DIR}/X64/EFI"))
    )
    return Path(replaced)


def is_user_file_in_downloads(path: Path) -> bool:
    download_path = user_path_to_download_path(path)
    result = download_path.exists()
    msg = (
        f"using {download_path}"
        if result
        else f"could not find a downloaded replacement for {path}"
    )
    fg = "green" if result else "yellow"
    click.echo(click.style(msg, fg=fg))
    return result


def user_or_updated(path: Path) -> Path:
    if is_user_file_in_downloads(path):
        name = Path(path).name
        click.echo(click.style("Will use updated " + name, fg="yellow"))
        output = user_path_to_download_path(path)
    else:
        output = Path(path)
    return output


def get_user_drivers_list_with_updates():
    user_drivers = get_user_drivers_list()
    return list(map(lambda driver: user_or_updated(driver), user_drivers))


def dprint(msg: str):
    border = '---------------------------'
    click.echo('\n')
    click.echo(click.style(border + msg + border,
               bg="black", fg="white", bold=True))
    click.echo('\n')


def print_start(name):
    return dprint(f'{name} START')


def print_done(name):
    return dprint(f'{name} DONE')


def update_local_efi_repository():
    print_start('update_local_efi_repository')
    os.system(f"cp -R {USER_EFI_DIR} {UPDATED_DIR}")
    click.echo(
        "will update user files and copy to updated directory and then to signed directory"
    )
    UPDATED_OC_DRIVERS_DIR = Path(f"{UPDATED_DIR}/EFI/OC/Drivers")
    for file in glob(f"{UPDATED_OC_DRIVERS_DIR}/*.efi"):
        os.remove(file)
        click.echo("Removed " + str(file))
    click.echo(
        "Finished purging all OpenCore drivers. Now inserting existing or updated if available"
    )
    user_drivers = get_user_drivers_list_with_updates()
    click.echo("user driver list with updates incorporated is:")
    pprint(user_drivers)
    for file in user_drivers:
        click.echo(f"copying {file} to {UPDATED_OC_DRIVERS_DIR}/{file.name}")
        os.system(f"cp -R {file} {UPDATED_OC_DRIVERS_DIR}/{file.name}")
    click.echo("Finished copying user files to updated directory")
    click.echo("Updated files are now:")
    # os.system(f'tree {UPDATED_DIR}')
    EFI_TEMP = f"{LOCAL_EFI_REPOSITORY}/EFI_TEMP"
    os.system(f"rm -rf {EFI_TEMP} > /dev/null")
    os.system(f"cp -R {USER_EFI_DIR}/* {EFI_TEMP}")
    os.system(f"rm -rf {USER_EFI_DIR} > /dev/null")
    os.system(f"cp -R {UPDATED_DIR}/* {USER_EFI_DIR}")
    click.echo(f'Removing {UPDATED_DIR}')
    os.system(f'rm -rf {UPDATED_DIR} > /dev/null')
    os.system("rm -rf {EFI_TEMP} > /dev/null")
    click.echo("Finished cleaning up EFI_TEMP. Opencore dir contents are now:")
    os.system(f"ls {USER_OPENCORE_DIR}")
    print_done('update_local_efi_repository')


def validate_config(vault: bool):
    # run ocvalidate
    ocvalidate_path = Path(f"{DOWNLOADS_DIR}/Utilities/ocvalidate/ocvalidate")
    config_path = config.get_config_path()
    Path.chmod(ocvalidate_path, 0o777)
    invalid = run([str(ocvalidate_path), config_path])
    if invalid:
        raise Exception(
            "ocvalidate returned a non-zero exit code. Please run ocvalidate manually for more information."
        )
    config_plist = config.parse_config_file(USER_OPENCORE_DIR)
    # check values for efi files
    drivers_list = list(map(lambda path: Path(
        path).name, get_user_drivers_list()))
    for driver in drivers_list:
        if driver not in list(
            map(lambda d: d["Path"], config_plist["UEFI"]["Drivers"])
        ):
            existing_drivers = config_plist["UEFI"]["Drivers"]
            existing_drivers.append(
                {"Arguments": "", "Comment": "", "Enabled": True, "Path": driver}
            )
            click.echo(click.style(
                f"will add {driver} to config", fg="yellow"))
            config_plist["UEFI"]["Drivers"] = existing_drivers
            config.write_config_file(config_plist, USER_OPENCORE_DIR)
        else:
            click.echo(
                click.style(
                    f"found driver {driver} in UEFI->Drivers", fg="green")
            )
    # check config_plist values for vault
    if vault:
        click.echo("Checking Apple Secure Boot configuration")
        if config_plist["Misc"]["Security"]["Vault"] != "Secure":
            raise Exception("Misc->Security->Vault is not set to Secure")
        else:
            click.echo("Misc->Security->Vault is set to Secure")
        # check values for windows dual boot
        if config_plist["Booter"]["Quirks"]["DevirtualiseMmio"] != True:
            raise Exception(
                "Booter->Quirks->DevirtualiseMmio is not set to True")
        else:
            click.echo("Booter->Quirks->DevirtualiseMmio is set to True")
        if config_plist["Booter"]["Quirks"]["ProtectUefiServices"] != True:
            raise Exception(
                "Booter->Quirks->ProtectUefiServices is not set to True")
        else:
            click.echo("Booter->Quirks->ProtectUefiServices is set to True")
        if config_plist["Booter"]["Quirks"]["SyncRuntimePermissions"] != True:
            raise Exception(
                "Booter->Quirks->SyncRuntimePermissions is not set to True")
        else:
            click.echo("Booter->Quirks->SyncRuntimePermissions is set to True")


def check_signed(files: list = []) -> bool:
    SIGNED_DIR = ENV["SIGNED_DIR"]
    code = 0
    if not len(files):
        raise Exception("check_signed was called with an empty list of files")
    for file in files:
        code += multipass(f"sbverify --list {file}")
        if not code == 0:
            raise Exception(f"{file} is not signed")
    return code == 0


def make_vault(signed: bool = True):
    click.echo(click.style("Making vault", bold=True))
    utilities = Path(DOWNLOADS_DIR / "Utilities/CreateVault")
    os.system(f"mkdir -pv {LOCAL_EFI_REPOSITORY}/Utilities")
    os.system(f"cp -R {utilities} {LOCAL_EFI_REPOSITORY}/Utilities")
    if signed:
        os.system(
            f"rm -rf {LOCAL_EFI_REPOSITORY}/EFI_TEMP && mkdir -p {LOCAL_EFI_REPOSITORY}/EFI_TEMP"
        )
        os.system(f"cp -R {USER_EFI_DIR}/* {LOCAL_EFI_REPOSITORY}/EFI_TEMP")
        os.system(f"cp -R {SIGNED_DIR}/* {USER_EFI_DIR}")
    utilities = Path(LOCAL_EFI_REPOSITORY / "Utilities")
    if not utilities.exists():
        raise Exception("could not find Utilities directory")
    path = utilities / "CreateVault" / "sign.command"
    output = run([f'{path}'])
    if signed:
        os.system(f"mv {USER_EFI_DIR} {SIGNED_DIR}")
        os.system(f"mv {LOCAL_EFI_REPOSITORY}/EFI_TEMP {USER_EFI_DIR}")
    os.system(f"rm -rf {utilities}")
    if output != 0:
        raise Exception("CreateVault returned a non-zero exit code")
    return output


def check_vault(signed: bool = True):
    dir = SIGNED_DIR if signed else USER_EFI_DIR
    files = list(map(lambda x: Path(dir) / "OC" /
                 x, ["vault.plist", "vault.sig"]))
    for file in files:
        if not file.exists():
            raise Exception("could not find " + str(file))


def download(url: str, dest_dir: str = ENV["DOWNLOADS_DIR"]):
    file_name = url.split("/")[-1]
    dest_path = Path(dest_dir) / file_name
    click.echo(click.style("Downloading " + url +
               " to " + str(dest_path), fg="green"))
    if dest_path.exists():
        click.echo("cleaning up " + str(dest_path) + " before downloading")
        os.remove(dest_path)
    response = requests.get(url, stream=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
    if not dest_path.exists():
        raise Exception("failed to download " + url)


def download_dependencies(version: str = VERSION, release: str = "RELEASE", binaries: bool = True):
    DOWNLOADS_DIR = Path(ENV["DOWNLOADS_DIR"])
    download(
        f"https://github.com/acidanthera/OpenCorePkg/releases/download/{version}/OpenCore-{version}-{release}.zip",
        ENV["DOWNLOADS_DIR"],
    )
    # unzip opencore
    run(
        [
            "/usr/bin/unzip",
            "-o",
            f"{str(DOWNLOADS_DIR)}/OpenCore-{version}-{release}.zip",
            "-d",
            str(DOWNLOADS_DIR),
        ]
    )
    if not Path(f"{DOWNLOADS_DIR}/X64/EFI/OC/OpenCore.efi").exists():
        raise Exception("could not find downloaded OpenCore.efi")
    else:
        click.echo("Successfully extracted OpenCore release")
    for file in glob(f"{DOWNLOADS_DIR}/*.zip"):
        click.echo("cleaning up " + str(file))
        os.remove(file)
    if binaries:
        download(
            "https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/HfsPlus.efi",
            str(USER_OPENCORE_DRIVERS_DIR),
        )
        download(
            "https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/ext4_x64.efi",
            str(USER_OPENCORE_DRIVERS_DIR),
        )


def check_keys():
    isk_files = list(map(lambda ext: KEYS_DIR / f"ISK.{ext}", ["key", "pem"]))
    for file in isk_files:
        if not file.exists():
            raise Exception("could not find " + str(file))
        click.echo("Found " + str(file))
    pass


def generate_apecid_partition():
    click.echo("generate_apeciding partition")
    return run(
        ['generate_apecid --folder "/System/Library/CoreServices" --bootefi --personalize']
    )


def mount_efi(name):
    cwd = os.getcwd()
    status = subprocess.run(
        [f"{cwd}/mountefi/MountEFI.command", name], check=True, env=ENV
    ).returncode
    if status != 0:
        raise Exception("MountEFI returned a non-zero exit code")
    return status


def unmount_efi(name):
    cwd = os.getcwd()
    status = subprocess.run(
        [f"{cwd}/mountefi/MountEFI.command", "-u", name], check=True, env=ENV
    ).returncode
    if status != 0:
        raise Exception(
            "MountEFI returned a non-zero exit code when attempting to unmount " + name
        )
    return status


def write_to_efi(src, dest):
    return copy_to_efi.copy_to_efi(src, dest)


@click.command()
@click.option("-V", "--version", default=VERSION, help=f'OpenCore version to use \(defaults to {VERSION}\)')
@click.option("-D", "--debug/--release", default=False, help=f'Use DEBUG build of OpenCore')
@click.option("-S", "--sign/--no-sign", default=False, help=f'Sign OpenCore')
@click.option("-V", "--vault/--no-vault", default=True, help=f'Create Apple Vault')
@click.option("-B", "--backup/--no-backup", default=False, help=f'Backup to the volume specified in environment variables')
@click.option("-W", "--write/--no-write", default=False, help=f'Write built files to EFI partition')
@click.option("-U", "--update/--no-update", default=True, help='Update local EFI repository using the downloaded version of OpenCore')
@click.option("-R", "--reset/--no-reset", default=False, help=f'Reset the local EFI repository using git before starting')
@click.option("-A", "--generate-apecid", default=False, help=f'Generate and insert apecid if necessary')
@click.option("-B", "--build/--no-build", default=True, help='Rebuild new EFI directory')
@click.option("-D", "--download/--skip-download", default=True, help='Download the specified version of OpenCore')
@click.option(
    "-S",
    "--backup-strategy",
    type=click.Choice(['local', 'volume'], case_sensitive=False),
    default="local",
    help="Backup strategy to use. Local backs up to a local 7z archive. Volume also backs up to a specified volume name"
)
@click.option("-C", "--commit", default=False, is_flag=True, help="Commit any changes to local EFI repository and push")
@click.option("--vault-only", default=False, is_flag=True, help="Commit any changes to local EFI repository and push")
def openchore(
    version: str = VERSION,
    debug: bool = False,
    sign: bool = False,
    vault: bool = True,
    backup: bool = False,
    write: bool = False,
    update: bool = True,
    reset: bool = False,
    generate_apecid: bool = False,
    build: bool = True,
    download: bool = True,
    backup_strategy: str = "local",
    commit: bool = False,
    vault_only: bool = False
):
    release = "DEBUG" if debug else "RELEASE"
    click.echo(click.style('Welcome to OpenChore!',
               bg='black', fg='white', bold=True))
    click.echo(click.style(
        f"Building OpenCore ({release}) {version}", fg="green", bold=True))
    if reset:
        cwd = os.getcwd()
        os.system(
            f"cd {LOCAL_EFI_REPOSITORY} && git add . && git reset HEAD --hard && cd {cwd}"
        )
        click.echo(click.style(
            "Finished resetting EFI folder", fg="green", bold=True))
    print_diagnostics(version, release, sign, vault, backup, write)
    create_directories()
    if backup:
        print("\n\n\n")
        click.echo(
            click.style(
                "Please enter the password for the currently logged in user to continue.",
                fg="green",
                bold=True,
            )
        )
        mount_efi(BOOT_VOLUME_NAME)
        # backup current efi to file
        click.echo("Backing up current EFI to " + str(BACKUP_DESTINATION))
        os.system(f"mkdir -p {BACKUP_DESTINATION}")
        os.system(f"rm -rf {BACKUP_DIR}/*")
        os.system(f"rsync -rvz --progress /Volumes/EFI/ {BACKUP_DESTINATION}")
        click.echo("Backed up current efi to {BACKUP_DESTINATION}")
        run([
            f"/usr/local/bin/7z a {BACKUP_DESTINATION}.7z {BACKUP_DESTINATION}"])
        unmount_efi(BOOT_VOLUME_NAME)
        if backup_strategy.to_lower() == 'local':
            click.echo("Cleaning up backup volume")
            mount_efi(BACKUP_VOLUME_NAME)
            os.system("rm -rf /Volumes/EFI/*")
            os.system("mkdir -p /Volumes/EFI/EFI")
            write_to_efi(str(BACKUP_DESTINATION), "/Volumes/EFI")
            click.echo("Copied to backup volume")
            unmount_efi(BACKUP_VOLUME_NAME)
    # TODO: do apecid
    # generate_apecid_partition()
    # download dependencies
    if download:
        binaries = vault_only == False
        download_dependencies(version, release, binaries)
    if not build and not vault_only:
        click.echo(
            click.style("Exiting (launched with '--no-build')")
        )
        return 0

    if generate_apecid:
        apecid.insert_apecid()
    # validate config.plist
    validate_config(vault)
    # updates
    if update and not vault_only:
        update_local_efi_repository()
        validate_config(vault)
    if build and sign and not vault_only:
        # sign opencore drivers for uefi secure boot
        check_keys()
        to_sign = glob(f"{USER_OPENCORE_DRIVERS_DIR}/*.efi") + glob(
            f"{USER_OPENCORE_DIR}/Tools/*.efi"
        )
        signlib.sign_all(to_sign, USER_EFI_DIR)
        signed_files = glob(f"{SIGNED_DIR}/OC/Drivers/*.efi")
        check_signed(signed_files)
        click.echo(click.style("Finished signing.", fg="green", bold=True))
    # create vault
    if vault or vault_only:
        make_vault(sign)

    # sign OpenCore EFI and BOOTx64.efi
    if build and sign:
        signlib.sign_opencore(USER_EFI_DIR)
        # TODO: (optional) create vault again?

    if commit:
        click.echo(click.style('Committing changes to local efi repository',
                   bg='red', fg='white', bold=True))
        cwd = os.getcwd()
        os.system(f'cd {LOCAL_EFI_REPOSITORY}')
        os.system(f'git add .')
        os.system(f'git commit -m "built OpenCore {version}"')
        os.system(f'git push')
        os.system(f'cd {cwd}')
    # mount efi
    if write:
        mount_efi(BOOT_VOLUME_NAME)
        path_to_copy = SIGNED_DIR if sign else USER_EFI_DIR
        write_to_efi(f"{path_to_copy}", "/Volumes/EFI")
        unmount_efi(BOOT_VOLUME_NAME)

    cleanup()
    click.echo(click.style("Done!", fg="green", bold=True, blink=True))


if __name__ == "__main__":
    openchore()
