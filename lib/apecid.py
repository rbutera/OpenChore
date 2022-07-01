import click
from lib import config, environment
ENV = environment.get_env()
APECID = ENV['APECID']


def get_apecid():
    config_plist = config.parse_config_file()
    return config_plist['Misc']['ApECID']


def check_if_apecid_exists():
    id = get_apecid()
    if not id or id == '':
        return False
    return True


def insert_apecid():
    if not check_if_apecid_exists():
        config_plist = config.parse_config_file()
        config_plist['Misc']['ApECID'] = APECID
        click.echo(style('WARNING: Inserting ApECID: ' +
                   APECID, fg='orange', bold=True))
        config.write_config_file(config_plist)
    else:
        click.echo('ApECID already exists. No need to insert.')
