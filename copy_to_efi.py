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


def clean(target):
    os.system(f'rm -rf {target}/*')
    path = target / "EFI"
    if not Path(path).exists():
        click.echo(f"creating {path}")
        Path.mkdir(path)
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        pass
    click.echo(f"Cleaned {path}")


def check_exists(input):
    msg = f"{input} is missing"
    if not Path(input).exists():
        raise Exception(msg)
    log.debug(f"Detected {input} exists")


def validate_input(path):
    path = Path(path / "EFI")
    oc = path / "OC"
    boot = path / "BOOT"
    x64 = boot / "BOOTx64.efi"
    opencore_efi = oc / "OpenCore.efi"
    config_plist = oc / "config.plist"

    for required in [oc, boot, x64, opencore_efi, config_plist]:
        check_exists(required)


def copy_to_efi(input: Path = USER_EFI_DIR, output: str = "/Volumes/EFI") -> int:
    input = Path(input)
    click.echo(f"copy_to_efi: Using source path {input}")
    if not Path(input).exists():
        raise Exception(f"source path {input} is missing")
    validate_input(input)
    output = Path(output)
    if not Path(output).exists():
        raise Exception(f'Missing destination volume "{output}"')

    clean(output)
    output = output / "EFI"
    log.debug(f"Cleaned. Time to copy to {output}...")
    code = os.system(
        f"rsync -rvz --progress --exclude='*.7z' {input}/* {output}/")
    log.debug(f"Exiting with code {code}")
    if code != 0:
        raise Exception(f"copy command returned non-zero code: {code}")
    click.echo("Completed successfully")
    return code


@click.command()
@click.option("--input_volume", default=USER_EFI_DIR, help=f"e.g. {USER_EFI_DIR}")
@click.option("--output_volume", default="/Volumes/EFI", help="e.g. /Volumes/EFI")
def main(input_volume, output_volume):
    return copy_to_efi(input_volume, output_volume)


if __name__ == "__main__":
    main()
