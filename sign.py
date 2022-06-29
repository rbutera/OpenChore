#!/usr/bin/env python
import environment
from pathlib import Path, PurePath
import click
from glob import glob
from run import multipass, run
import os
ENV = environment.get_env()

SIGNED_DIR = Path(ENV['SIGNED_DIR'])
UPDATED_DIR = Path(ENV['UPDATED_DIR'])
KEYS_DIR = Path(ENV['KEYS_DIR'])
ISK_pem = Path(f'{KEYS_DIR}/ISK.pem')
ISK_key = Path(f'{KEYS_DIR}/ISK.key')


def sign_file(input: Path, output: Path) -> int:
    click.echo(click.style(
        'will sign {} to {}'.format(input, output), fg='yellow'))
    run(['rm', '-rfv', f'{output}'])
    os.system('mkdir -pv {}'.format(output.parent))
    multipass(
        f'sbsign --key {ISK_key} --cert {ISK_pem} --output {output} {input}')


def sign_opencore(base_dir) -> int:
    bootx64 = Path(f'{base_dir}/BOOT/BOOTx64.efi')
    opencore_efi = Path(f'{base_dir}/OC/OpenCore.efi')
    sign_file(opencore_efi, SIGNED_DIR / 'OC/OpenCore.efi')
    sign_file(bootx64, SIGNED_DIR / 'BOOT/BOOTx64.efi')


def sign_all(files, base_path) -> int:
    '''
        signs all the files in the file list, to the same relative path in the signed directory
    '''
    for file in files:
        relative_path = PurePath(f'{file}').relative_to(base_path)
        sign_file(file, Path(f'{SIGNED_DIR}/{relative_path}'))
