#!/usr/bin/env python3
from os.path import isdir
import shutil
import sys

from telemetry.telescope_devkit.cli import cli, get_console
from telemetry.telescope_devkit.ec2 import Ec2Cli
from telemetry.telescope_devkit.elasticsearch import ElasticsearchCli
from telemetry.telescope_devkit.logs import LogsCli
from telemetry.telescope_devkit.migration.cli import Phase1Cli, Phase2Cli, Phase3Cli

commands = {
    'ec2': Ec2Cli,
    'elasticsearch': ElasticsearchCli,
    'logs': LogsCli,
    'migration' : {
        'phase-1': Phase1Cli,
        'phase-2': Phase2Cli,
        'phase-3': Phase3Cli
    }
}


def is_running_in_docker() -> bool:
    with open('/proc/1/cgroup', 'rt') as ifh:
        return 'docker' in ifh.read()


def setup_ssh_config():
    if not isdir("/root/.ssh"):
        shutil.copytree("/root/.ssh_host", "/root/.ssh")


if __name__ == '__main__':
    try:
        if is_running_in_docker():
            setup_ssh_config()
        exit_code = cli(commands, name='telescope')
        if isinstance(exit_code, int):
            sys.exit(exit_code)
    except Exception as e:
        get_console().print_exception()
