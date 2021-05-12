#!/usr/bin/env python3
from telemetry.telescope_devkit.cli import cli, get_console
from telemetry.telescope_devkit.devkit import DevkitCli
from telemetry.telescope_devkit.ec2 import Ec2Cli
from telemetry.telescope_devkit.elasticsearch import ElasticsearchCli
from telemetry.telescope_devkit.logger import create_app_logger
from telemetry.telescope_devkit.logs import LogsCli

commands = {
    'ec2': Ec2Cli,
    'logs': LogsCli,
    'elasticsearch': ElasticsearchCli,
    'self-update': DevkitCli.update
}

if __name__ == '__main__':
    create_app_logger()
    try:
        cli(commands, name='telescope')
    except Exception as e:
        get_console().print_exception(e)
