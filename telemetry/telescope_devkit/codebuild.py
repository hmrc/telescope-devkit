import boto3

from telemetry.telescope_devkit.cli import get_console


class Codebuild(object):
    def __init__(self):
        self._client = boto3.client("codebuild")

    def start_build(self, project_name: str):
        return self._client.start_build(projectName=project_name)


class CodebuildCli(object):
    def __init__(self):
        self._console = get_console()
        self._codebuild = Codebuild()

    def deploy_kibana_dashboards(self):
        self._console.print("Deploying Kibana dashboards...")
        result = self._codebuild.start_build("deploy-kibana-dashboards")
        self._console.print(result)

    def deploy_grafana_dashboards(self):
        self._console.print("Deploying Grafana dashboards...")
        result = self._codebuild.start_build("grafana-dashboards-deploy")
        self._console.print(result)
