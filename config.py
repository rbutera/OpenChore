#!/usr/bin/env python
from pathlib import Path
import os
import click
import plistlib
import environment
ENV = environment.get_env()
USER_OPENCORE_DIR = Path(ENV['USER_OPENCORE_DIR'])
DOWNLOADS_DIR = Path(ENV['DOWNLOADS_DIR'])


def get_config_path(dir: Path = USER_OPENCORE_DIR):
    config_plist = Path(f'{dir}/config.plist')
    print(f'checking if {config_plist} exists')
    if not Path(config_plist).exists():
        raise Exception('could not find config.plist')
    return config_plist


def open_config(dir: Path = USER_OPENCORE_DIR):
    path = get_config_path(dir)
    return open(path, 'r+')


def parse_config_file(dir: Path = USER_OPENCORE_DIR):
    config_plist = open_config(dir)
    output = plistlib.load(config_plist, fmt="FMT_XML")
    config_plist.close()
    return output


def write_config_file(config: dict, dir: Path = USER_OPENCORE_DIR):
    out = Path(f'{dir}/config.plist')
    if Path(out).exists():
        os.remove(out)
    fp = open(out, 'wb')
    plistlib.dump(config, fp, fmt="FMT_XML", sort_keys=False)
