import boto3
from boto3.session import Session

from telemetry.telescope_devkit.cli import get_console


class Codebuild(object):
    def __init__(self):
        self._client = boto3.client("codebuild")

    def get_latest_terraform_build_id(self, project_name: str, session: Session) -> str:
        codebuild_session = session.client("codebuild")
        builds = codebuild_session.list_builds_for_project(projectName=project_name)
        return builds['ids'][0]

    def get_terraform_build_status(self, project_id: str, session: Session) -> str:
        codebuild_session = session.client("codebuild")
        builds = codebuild_session.batch_get_builds(ids=[project_id])
        return builds['builds'][0]['buildStatus']

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
        result = self._codebuild.start_build("deploy-grafana-dashboards")
        self._console.print(result)
