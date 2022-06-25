#!/usr/bin/env python

from dotenv import load_dotenv
from pprint import pprint
load_dotenv()

ENV = {}


def build_env():
    global ENV
    ENV = os.environ.copy()
    ENV['KEYS_DIR'] = ENV["HACKINTOSH_ROOT"] + "/keys"
    ENV['SIGNED_DIR'] = ENV["HACKINTOSH_ROOT"] + "/signed"
    ENV['DOWNLOADS_DIR'] = ENV["HACKINTOSH_ROOT"] + "/download"
    ENV['DOWNLOADED_EFI_DIR'] = ENV["$DOWNLOADS_DIR"] + "/X64/EFI"
    ENV['USER_EFI_DIR'] = ENV["HACKINTOSH_ROOT"] + "/EFI"
    ENV['USER_OPENCORE_DIR'] = ENV["USER_EFI_DIR"] + "/OC"
    ENV['USER_OPENCORE_DRIVERS_DIR'] = ENV["USER_OPENCORE_DIR"] + "/Drivers"
    return ENV


def get_env():
    if len(ENV) == 0:
        print('ENV is empty, calling build_env()')
        return build_env()
    return ENV


if __name__ == '__main__':
    get_env()
    pprint(ENV)
