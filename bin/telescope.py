#!/usr/bin/env python3
import os.path
from os.path import isdir
import shutil
import sys
from telemetry.telescope_devkit.multiaccount import MultiAccountCli

from telemetry.telescope_devkit.asg import AsgCli
from telemetry.telescope_devkit.cli import cli, get_console
from telemetry.telescope_devkit.codebuild import CodebuildCli
from telemetry.telescope_devkit.ec2 import Ec2Cli
from telemetry.telescope_devkit.elasticsearch import ElasticsearchCli
from telemetry.telescope_devkit.logs import LogsCli
from telemetry.telescope_devkit.migration.cli import Phase1Cli, Phase2PreCutoverCli, Phase2PostCutoverCli, Phase3Cli
from telemetry.telescope_devkit.sts import StsCli

commands = {
    'asg': AsgCli,
    'codebuild': CodebuildCli,
    'ec2': Ec2Cli,
    'elasticsearch': ElasticsearchCli,
    'logs': LogsCli,
    'migration' : {
        'phase-1': Phase1Cli,
        'phase-2-pre-cutover': Phase2PreCutoverCli,
        'phase-2-post-cutover': Phase2PostCutoverCli,
        'phase-3': Phase3Cli
    },
    # 'multiaccount': MultiAccountCli,
    'sts': StsCli
}
# print(commands)
# commands['multiaccount'] = MultiAccountCli(commands)
# print(commands)
# exit()

def is_running_in_docker() -> bool:
    if not os.path.isfile('/proc/1/cgroup'):
        return False

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
