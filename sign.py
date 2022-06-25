#!/usr/bin/env python
import environment
from pathlib import Path
from click import *
from glob import glob
from run import multipass, run
ENV = environment.get_env()

SIGNED_DIR = Path(ENV['SIGNED_DIR'])
UPDATED_DIR = Path(ENV['UPDATED_DIR'])
KEYS_DIR = Path(ENV['KEYS_DIR'])
ISK_pem = KEYS_DIR / 'ISK.pem'
ISK_key = KEYS_DIR / 'ISK.key'


def sign_file(input: Path, output: Path) -> int:
    echo(style('will sign {} to {}'.format(input, output)))
    run(['rm', '-rfv', output])
    run.multipass(
        f'sbsign --key {ISK_key} --cert {ISK_pem} --output {output} {input}')


def sign_opencore(base_dir) -> int:
    bootx64 = base_dir / 'BOOT/BOOTx64.efi'
    opencore_efi = base_dir / 'OC/OpenCore.efi'
    sign_file(opencore_efi, SIGNED_DIR / 'OC/OpenCore.efi')
    sign_file(bootx64, SIGNED_DIR / 'BOOT/BOOTx64.efi')


def sign_all(files, base_path) -> int:
    '''
        signs all the files in the file list, to the same relative path in the signed directory
    '''
    for file in files:
        sign_file(file, SIGNED_DIR / file.relative_to(base_path))
