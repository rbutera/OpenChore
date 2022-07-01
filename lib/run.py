#!/usr/bin/env python
import subprocess
import os
from lib import environment
from pprint import pprint
from click import echo
ENV = environment.get_env()


def run(commands: list[str]) -> int:
    commands = map(lambda x: str(x), commands)
    commands = list(commands)
    commands = ' '.join(commands)
    commands = f'"{commands}"'
    input = ['/bin/zsh', '-c', commands]
    input_str = ' '.join(input)
    echo(f'will run "{input_str}"')
    completed = subprocess.run(input_str, shell=True, env=ENV, check=True)
    print(completed)
    return completed.returncode


def multipass(command: str) -> int:
    mn = ENV["MULTIPASS_NAME"]
    return run([f"multipass exec {mn} -- sh -c '{command}'"])
