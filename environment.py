#!/usr/bin/env python
import os
from dotenv import load_dotenv, dotenv_values
from pprint import pprint
load_dotenv()

ENV = {}


def build_env():
    global ENV
    values = dotenv_values(".env").items()
    for key, value in values:
        ENV[key] = value

    ENV['KEYS_DIR'] = ENV["HACKINTOSH_ROOT"] + "/keys"
    ENV['SIGNED_DIR'] = ENV["HACKINTOSH_ROOT"] + "/signed"
    ENV['DOWNLOADS_DIR'] = ENV["HACKINTOSH_ROOT"] + "/download"
    ENV['DOWNLOADED_EFI_DIR'] = ENV["DOWNLOADS_DIR"] + "/X64/EFI"
    ENV['USER_EFI_DIR'] = ENV["HACKINTOSH_ROOT"] + "/EFI"
    ENV['USER_OPENCORE_DIR'] = ENV["USER_EFI_DIR"] + "/OC"
    ENV['USER_OPENCORE_DRIVERS_DIR'] = ENV["USER_OPENCORE_DIR"] + "/Drivers"
    ENV['PATH'] = os.getenv('PATH')
    if 'BACKUP_DIR' not in ENV.keys():
        ENV['BACKUP_DIR'] = os.getcwd() + "/backup"

    return ENV


def get_env():
    if len(ENV) == 0:
        # print('ENV is empty, calling build_env()')
        return build_env()
    return ENV


if __name__ == '__main__':
    get_env()
    pprint(ENV)
