import shlex
import socket
import subprocess
from contextlib import closing

from telemetry.telescope_devkit.cli import get_console


class LocalPortForwarding(object):
    def __init__(
        self,
        ssh_server: str,
        destination_host: str,
        destination_port: int,
        local_host="0.0.0.0",
        local_port=None,
    ):
        self.ssh_server = ssh_server
        self.destination_host = destination_host
        self.destination_port = destination_port
        self.local_host = local_host
        self.local_port = destination_port if local_port is None else local_port
        self._console = get_console()

    def start(self) -> int:
        cmd = f"ssh -L {self.local_host}:{self.local_port}:{self.destination_host}:{self.destination_port} -f -N {self.ssh_server}"
        self._console.print(f"[cyan]EXEC: {cmd}[/cyan]")
        return subprocess.run(shlex.split(cmd)).returncode

    def stop(self) -> int:
        cmd = f"ssh -O cancel -L {self.local_host}:{self.local_port}:{self.destination_host}:{self.destination_port} {self.ssh_server}"
        self._console.print(f"[cyan]EXEC: {cmd}[/cyan]")
        return subprocess.run(shlex.split(cmd)).returncode

    def is_service_reachable(self) -> bool:
        try:
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
                return sock.connect_ex((self.local_host, self.local_port)) == 0
        except OSError as e:
            self._console.print_exception()
            return False


def ssh_to(ip_address: str) -> int:
    completed_process = subprocess.run(["ssh", ip_address])
    return completed_process.returncode
