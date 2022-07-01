#!/usr/bin/env python
from pathlib import Path
import os
import plistlib
from lib import environment
ENV = environment.get_env()
USER_OPENCORE_DIR = Path(ENV['USER_OPENCORE_DIR'])
DOWNLOADS_DIR = Path(ENV['DOWNLOADS_DIR'])


def get_config_path(dir: Path = USER_OPENCORE_DIR):
    config_plist = Path(f'{dir}/config.plist')
    print(f'checking if {config_plist} exists')
    if not Path(config_plist).exists():
        raise Exception('could not find config.plist')
    return config_plist


def parse_config_file(dir: Path = USER_OPENCORE_DIR):
    config_plist = get_config_path(dir)
    config_plist = open(config_plist, 'rb')
    output = plistlib.load(config_plist, fmt=plistlib.FMT_XML)
    config_plist.close()
    return output


def write_config_file(config: dict, dir: Path = USER_OPENCORE_DIR):
    out = Path(f'{dir}/config.plist')
    if Path(out).exists():
        os.remove(out)
    fp = out.open('wb')
    plistlib.dump(config, fp, fmt=plistlib.FMT_XML, sort_keys=False)
