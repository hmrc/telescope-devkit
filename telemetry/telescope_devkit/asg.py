import boto3

from telemetry.telescope_devkit.cli import get_console
from rich.table import Table

class Asg(object):
    def __init__(self):
        self.autoscaling_client = boto3.client('autoscaling', region_name='eu-west-2')

    def get_telemetry_asgs(self):
        response = self.autoscaling_client.describe_auto_scaling_groups(
            MaxRecords = 100
        )

        paginator = self.autoscaling_client.get_paginator('describe_auto_scaling_groups')
        page_iterator = paginator.paginate(
            PaginationConfig={'PageSize': 100}
        )

        return page_iterator.search(
            'AutoScalingGroups[] | [?contains(Tags[?Key==`sensu-team-handler`].Value, `team-telemetry`)]'
        )







class AsgCli(object):
    def __init__(self):
        self._console = get_console()
        self._asg = Asg()

    def telemetry_asgs(self):
        filtered_asgs = self._asg.get_telemetry_asgs()

        table = Table(show_header=True, header_style="bold green")
        table.add_column('AutoScalingGroupName')
        table.add_column('DesiredCapacity')
        table.add_column('MinSize')
        table.add_column('MaxSize')
        table.add_column('Instance Type')

        for asg in filtered_asgs:
            if asg['Instances']:
                table.add_row(
                    asg['AutoScalingGroupName'],
                    str(asg['DesiredCapacity']),
                    str(asg['MinSize']),
                    str(asg['MaxSize']),
                    asg['Instances'][0]['InstanceType']
                )
        self._console.print(table)


