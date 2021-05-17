import shlex
import subprocess

import docker


class DockerClient(object):
    def __init__(self):
        self._client = docker.from_env()
        assert self._client.ping() is True

    def run(self, image, command=None, stdout=True, stderr=True, remove=True, **kwargs):
        return self._client.containers.run(
            image, command, stdout, stderr, remove, **kwargs
        )

    def run_interactive_legacy(
        self, image, command=None, volumes=None, ports=None, environment=None
    ):
        cmd = f"docker run"

        if environment is not None:
            for k, v in environment.items():
                cmd += f" -e {k}={v}"

        if volumes is not None:
            for k, v in volumes.items():
                cmd += f" -v {k}:{v}"

        if ports is not None:
            for k, v in ports.items():
                cmd += f" -p {k}:{v}"

        cmd += f" --rm -it {image}"

        if command is not None:
            cmd += f" {command}"

        return subprocess.run(shlex.split(cmd)).returncode
