#!/usr/bin/env python
import subprocess
import os
import environment
from pprint import pprint
from click import echo
ENV = environment.get_env()


def run(commands: list[str]) -> int:
    print('env is:')
    pprint(ENV)
    commands = map(lambda x: str(x), commands)
    commands = list(commands)
    commands = ' '.join(commands)
    commands = f"'{commands}'"
    input = ['/bin/zsh', '-c', commands]
    input_str = ' '.join(input)
    echo(f'will run "{input_str}"')
    os.system(input_str)


def multipass(command: str) -> int:
    mn = ENV["MULTIPASS_NAME"]
    return run([f"multipass {mn} exec sh -c '{command}'"])
