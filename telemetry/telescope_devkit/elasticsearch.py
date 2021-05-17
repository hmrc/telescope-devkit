import json
import os

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.docker import DockerClient
from telemetry.telescope_devkit.ec2 import Ec2
from telemetry.telescope_devkit.filesystem import get_repo_path
from telemetry.telescope_devkit.ssh import LocalPortForwarding
from telemetry.telescope_devkit.sts import Sts


class Comrade(object):
    def __init__(self):
        self._console = get_console()
        self._ec2 = Ec2()
        self._sts = Sts()
        self._docker = DockerClient()
        self._clusters_data_dir = os.path.join(
            get_repo_path(), "data/elasticsearch-comrade"
        )
        self._use_docker_py = False

    def run(self):
        instance_name = "elasticsearch-master"
        instance = self._ec2.get_instance_by_name(instance_name, enable_wildcard=False)

        if not instance:
            self._console.print(
                f"[red]ERROR: No '{instance_name}' instances found in this account[/red]"
            )
            return 1

        ssh_server_ip_address = instance["PrivateIpAddress"]
        with self._console.status(
            f"[bold green]Setting up an SSH tunnel to elasticsearch:9200 via {ssh_server_ip_address}... "
        ) as status:
            tunnel = LocalPortForwarding(ssh_server_ip_address, "elasticsearch", 9200)
            tunnel.start()

        if not tunnel.is_service_reachable():
            self._console.print(f"Unable to reach remote service via localhost:9200")
            tunnel.stop()
            return 1

        self._generate_cluster_config()
        self._console.print(
            f"Launching the elasticsearch-comrade Docker container...\nPress [yellow]<ctrl-c>[/yellow] to stop it."
        )
        container = None
        try:
            if self._use_docker_py:
                container = self._docker.run(
                    image="mosheza/elasticsearch-comrade",
                    ports={8000: 8000},
                    volumes={
                        self._clusters_data_dir: {
                            "bind": "/app/comrade/clusters/",
                            "mode": "rw",
                        }
                    },
                    environment={"COMRADE_DEBUG": "true"},
                    tty=True,
                    auto_remove=True,
                    remove=True,
                    detach=True,
                )
                while True:
                    for output in container.logs(stream=True):
                        print(output.decode("utf-8"), end="")
            else:
                self._docker.run_interactive_legacy(
                    image="mosheza/elasticsearch-comrade",
                    ports={8000: 8000},
                    volumes={self._clusters_data_dir: "/app/comrade/clusters/"},
                    environment={"COMRADE_DEBUG": "true"},
                )
        except KeyboardInterrupt:
            if container:
                self._console.print("Stopping the Docker container...")
                container.stop()

        if not os.path.isdir(self._clusters_data_dir):
            os.makedirs(self._clusters_data_dir)
            self._console.print(f"Created directory '{self._clusters_data_dir}'")

        with self._console.status(
            f"[bold green]Stopping SSH tunnel to elasticsearch:9200 via {ssh_server_ip_address}..."
        ) as status:
            tunnel.stop()

    def _generate_cluster_config(self):
        scheme = "http" if self._sts.is_webops_account else "https"
        config = {
            "name": f"ElasticSearch @ {self._sts.account_name}",
            "params": {
                "hosts": [f"{scheme}://host.docker.internal:9200"],
                "ca_certs": False,
                "verify_certs": False,
            },
        }

        with open(os.path.join(self._clusters_data_dir, "cluster.json"), "w") as file:
            json.dump(config, file, indent=4, sort_keys=True)


class ElasticsearchCli(object):
    def __init__(self):
        self._comrade = Comrade()

    def comrade(self):
        self._comrade.run()
