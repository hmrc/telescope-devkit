import boto3
from rich.table import Table

from telemetry.telescope_devkit.cli import get_console


class Asg(object):
    def __init__(self):
        self.autoscaling_client = boto3.client("autoscaling", region_name="eu-west-2")

    def get_telemetry_asgs(self):
        paginator = self.autoscaling_client.get_paginator(
            "describe_auto_scaling_groups"
        )
        page_iterator = paginator.paginate(PaginationConfig={"PageSize": 100})

        return page_iterator.search(
            "AutoScalingGroups[] | [?contains(Tags[?Key==`sensu-team-handler`].Value, `team-telemetry`)]"
        )


class AsgCli(object):
    def __init__(self):
        self._console = get_console()
        self._asg = Asg()

    def all_telemetry(self):
        """
        Fetch details for all Telemetry ASGs running in a given environment
        """
        table = Table(show_header=True, header_style="bold green")
        table.add_column("ASG Name")
        table.add_column("Desired Capacity")
        table.add_column("Min Size")
        table.add_column("Max Size")
        table.add_column("Instance Type")

        for asg in self._asg.get_telemetry_asgs():
            if asg["Instances"]:
                table.add_row(
                    asg["AutoScalingGroupName"],
                    str(asg["DesiredCapacity"]),
                    str(asg["MinSize"]),
                    str(asg["MaxSize"]),
                    asg["Instances"][0]["InstanceType"],
                )
        self._console.print(table)
