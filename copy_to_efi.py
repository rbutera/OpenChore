#!/usr/bin/env python
import click
from glob import glob
import logging as log
import os
import shutil
from pathlib import Path
import environment
ENV = environment.get_env()
USER_EFI_DIR = ENV['USER_EFI_DIR']
SIGNED_DIR = ENV['SIGNED_DIR']


cwd = Path.cwd()
log.debug(f"Current working directory is {cwd}")


def clean_dest(volume_path):
    path = volume_path / "EFI"
    if not Path.exists(path):
        click.echo(f"creating {path}")
        Path.mkdir(path)
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    click.echo(f"Cleaned {path}")


def check_exists(input):
    if not Path.exists(input):
        raise Exception(f"{input} is missing")
    log.debug(f"Detected {input} exists")


def check_src(input_dir):
    oc = input_dir / "OC"
    boot = input_dir / "BOOT"
    x64 = boot / "BOOTx64.efi"
    opencore_efi = oc / "OpenCore.efi"
    config_plist = oc / "config.plist"

    for required in [oc, boot, x64, opencore_efi, config_plist]:
        check_exists(required)


@click.command()
@click.option("--input_volume", default=USER_EFI_DIR, help=f"e.g. {USER_EFI_DIR}")
@click.option("--output_volume", default="/Volumes/EFI", help="e.g. /Volumes/EFI")
def copy_to_efi(input_dir: Path = USER_EFI_DIR, output_volume: str = "/Volumes/EFI") -> int:
    src_path = Path(input_dir)
    click.echo(f"{message}\nUsing source path {src_path}")
    if not Path.exists(src_path):
        raise Exception(f"source path {src_path} is missing")
    check_src(src_path)
    dest_path = Path(output_volume)
    if not Path.exists(dest_path):
        raise Exception(f'Missing destination volume "{output_volume}"')

    clean_dest(dest_path)
    dest_path = dest_path / "EFI"
    log.debug(f"Cleaned. Time to copy to {dest_path}...")
    code = os.system(f"rsync -rvz --progress {src_path}/* {dest_path}/")
    log.debug(f"Exiting with code {code}")
    if code != 0:
        raise Exception(f"copy command returned non-zero code: {code}")
    click.echo("Completed successfully")
    return code


if __name__ == "__main__":
    copy_to_efi()
