from typing import Union

import boto3
from mypy_boto3_ec2.service_resource import ServiceResourceInstancesCollection, Instance

from rich.table import Table

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.ssh import ssh_to, LocalPortForwarding


class Ec2(object):
    def __init__(self):
        """
        See https://boto3.amazonaws.com/v1/documentation/api/1.17.74/reference/services/ec2.html#EC2.ServiceResource.instances
        """
        self._ec2_resource_service_client = boto3.resource("ec2")

    def get_instances_by_name(
        self, name: str, enable_wildcard: bool = True
    ) -> ServiceResourceInstancesCollection:
        if enable_wildcard:
            name = "*" + name + "*"

        return self._ec2_resource_service_client.instances.filter(
            Filters=[
                {"Name": "tag:Name", "Values": [name]},
                {"Name": "instance-state-name", "Values": ["running"]},
            ]
        )

    def get_instance_by_name(
        self, name: str, enable_wildcard: bool = True
    ) -> Union[Instance, None]:
        for instance in self.get_instances_by_name(name, enable_wildcard):
            return instance


class Ec2Cli(object):
    def __init__(self):
        self._console = get_console()
        self._ec2 = Ec2()

    def instances(self, name: str, enable_wildcard: bool = True) -> None:
        with self._console.status("[bold green]Fetching instances info...") as status:
            instances = self._ec2.get_instances_by_name(name, enable_wildcard)
            self._render_instances(instances)

    def ssh(self, instance_name: str, enable_wildcard: bool = True) -> int:
        """SSH to the first EC2 instances that matches the name filter given."""
        with self._console.status(
            "[bold green]Fetching instance IP address..."
        ) as status:
            instance = self._ec2.get_instance_by_name(instance_name, enable_wildcard)

        if not instance:
            self._console.print(
                f"[red]ERROR: No '{instance_name}' instances found in this account[/red]"
            )
            return 1

        ip_address = instance.private_ip_address
        self._console.print(f"[bold green]Connecting to {ip_address}...")
        return ssh_to(ip_address)

    def tunnel(self, instance_name: str, host: str, port: int) -> int:
        with self._console.status(
            "[bold green]Fetching instance IP address..."
        ) as status:
            instance = self._ec2.get_instance_by_name(
                instance_name, enable_wildcard=False
            )

        if not instance:
            self._console.print(
                f"[red]ERROR: No '{instance_name}' instances found in this account[/red]"
            )
            return 1

        ssh_server_ip_address = instance.private_ip_address
        local_host = "localhost"
        with self._console.status(
            f"[bold green]Setting up an SSH tunnel to {host}:{port} via {ssh_server_ip_address}... "
        ) as status:
            tunnel = LocalPortForwarding(
                ssh_server_ip_address,
                destination_host=host,
                destination_port=port,
                local_host=local_host,
            )
            tunnel.start()

        if not tunnel.is_service_reachable():
            self._console.print(
                f"Unable to reach remote service via {local_host}:{port}"
            )
            tunnel.stop()
            return 1

        if host != local_host:
            self._console.print(
                f"If you need to access this service via {host} instead of {local_host} make sure to "
                f"add an entry in the /etc/hosts file"
            )

        self._console.input(
            "\nPress [yellow]<Enter>[/yellow] at any time to stop the SSH tunnel... "
        )

        with self._console.status(
            f"[bold green]Stopping SSH tunnel to {host}:{port} via {ssh_server_ip_address}..."
        ) as status:
            tunnel.stop()

        return 0

    def _render_instances(self, instances: ServiceResourceInstancesCollection):
        if len(list(instances)) <= 0:
            self._console.print(
                "[bright_yellow]⚠ There are no EC2 instances running in this account.[/bright_yellow]"
            )
            return

        table = Table(show_header=True, header_style="bold green")
        table.add_column("Instance Name")
        table.add_column("Instance Id")
        table.add_column("Instance Type")
        table.add_column("Availability Zone")
        table.add_column("Launch Time")
        table.add_column("Private IP Address")
        for instance in instances:
            # See https://boto3.amazonaws.com/v1/documentation/api/1.17.74/reference/services/ec2.html#EC2.ServiceResource.Instance
            instance_name = [
                tag["Value"] for tag in instance.tags if tag["Key"] == "Name"
            ][0]
            table.add_row(
                instance_name,
                instance.instance_id,
                instance.instance_type,
                instance.placement["AvailabilityZone"],
                instance.launch_time.strftime("%Y-%m-%d %H:%M:%S"),
                instance.private_ip_address,
            )
        self._console.print(table)
