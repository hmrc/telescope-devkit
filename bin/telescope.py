#!/usr/bin/env python3
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

if __name__ == '__main__':
    try:
        exit_code = cli(commands, name='telescope')
        if isinstance(exit_code, int):
            sys.exit(exit_code)
    except Exception as e:
        get_console().print_exception()
