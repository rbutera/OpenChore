#!/usr/bin/env python
import subprocess
import environment
from click import echo
ENV = environment.get_env()


def run(commands: list[str]) -> int:
    commands = map(lambda x: str(x), commands)
    commands = list(commands)
    commands = ' '.join(commands)
    commands = f"'{commands}'"
    input = ['/bin/bash', '-c', commands]
    input_str = ' '.join(input)
    echo(f'will run "{input_str}"')
    return subprocess.run(input, check=True, env=ENV).returncode


def multipass(command: str) -> int:
    return run(['-c', f"multipass exec sh -c '{command}'"], check=True, env=ENV).returncode
