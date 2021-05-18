import json
import shlex
import subprocess

import requests
from rich.prompt import Prompt

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.ec2 import Ec2
from telemetry.telescope_devkit.logger import create_file_logger
from telemetry.telescope_devkit.grafana import Grafana
from telemetry.telescope_devkit.sts import Sts, get_account_name


def create_migration_checklist_logger():
    account_name = Sts().account_name
    logger = create_file_logger(f"{account_name}-migration-checklist.log")
    get_console().print(
        f"* Check activity is being logged to [blue]log/{account_name}-migration-checklist.log[/blue]"
    )

    return logger


class NotImplementedException(Exception):
    pass


class Check(object):
    _description = None
    _is_successful = None
    _requires_manual_intervention = False
    _console = get_console()
    _sts = Sts()
    _logger = None

    def check(self):
        raise NotImplementedException

    def check_interactively(self):
        raise NotImplementedException

    @property
    def description(self) -> str:
        return self._description

    def is_successful(self) -> bool:
        return self._is_successful

    def requires_manual_intervention(self) -> bool:
        return self._requires_manual_intervention

    def launch_manual_intervention_prompt(self):
        result = Prompt.ask(
            "Please enter the result for this check",
            choices=["pass", "fail"],
            default="fail",
        )
        self._is_successful = True if result == "pass" else False

    @property
    def logger(self):
        if self._logger is None:
            self._logger = create_migration_checklist_logger()
        return self._logger


class TerraformBuild(Check):
    _description = "Terraform Build job is green"
    _requires_manual_intervention = True

    def check(self):
        pass

    def check_interactively(self):
        self._console.print(
            f"""  Visit https://eu-west-2.console.aws.amazon.com/codesuite/codebuild/634456480543/projects/build-telemetry-{get_account_name()}-terraform/history?region=eu-west-2
  and inspect the result of the last Terraform run."""
        )
        self.launch_manual_intervention_prompt()


class EcsStatusChecks(Check):
    _description = "ECS Status Checks are green"

    def check(self):
        ec2 = Ec2()
        instance = ec2.get_instance_by_name(name="telemetry", enable_wildcard=False)
        # get the ecs status check result
        cmd = f"ssh {instance['PrivateIpAddress']} curl http://ecs-status-checks.telemetry.internal:5000/test -s -o /dev/null -I -w \"%{{http_code}}\""
        completed_process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        return_code = completed_process.stdout.decode("utf-8")
        if return_code == "200":
            self._is_successful = True
            return

        self._is_successful = False
        # return to the user the details ecs status check results
        self.logger.debug(f"ECS Status Checks returned status code {return_code}")
        self.logger.debug("detailed result of ecs-status-checks:")
        cmd = f"ssh {instance['PrivateIpAddress']} curl http://ecs-status-checks.telemetry.internal:5000 -s"
        completed_process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        response = json.loads(completed_process.stdout)
        self.logger.debug(json.dumps(response, indent=4))


class KafkaLogsConsumption(Check):
    _description = "Kafka logs consumption looks correct"

    def check(self):
        grafana = Grafana(
            hostname=f"grafana.{self._sts.account_name}.telemetry.tax.service.gov.uk"
        )

        # Validate that all partitions have an offset greater than 0
        self.logger.debug("Validate that all partitions have an offset greater than 0")
        metric_query = "aliasByNode(telemetry.telescope.msk.metrics.*.offset%2C%204)&from=-5min&until=now&format=json&maxDataPoints=1"
        data = grafana.get_metric_value(metric_query=metric_query)

        for partition in data:
            if int(partition["datapoints"][0][0]) < 0:
                self.logger.debug(
                    f"{partition['target']} has an offset of {partition['datapoints'][0][0]} which is an error code"
                )
                self._is_successful = False
                return

        # Validate that all consumers are up to date
        msk_consumer_groups = ["metrics", "logs"]
        msk_log_retention_period = "1h"
        lag_threshold = 30
        for msk_consumer_group in msk_consumer_groups:
            metric_query = f"alias(offset(scale(keepLastValue(divideSeries(telemetry.telescope.msk.{msk_consumer_group}.sum-lag%2Ctelemetry.telescope.msk.{msk_consumer_group}.sum-range)%2C%2060)%2C%20-100)%2C%20100)%2C%20'Offset')&from=-{msk_log_retention_period}&until=now&format=json&maxDataPoints=1"
            data = grafana.get_metric_value(metric_query=metric_query)
            if int(data[0]["datapoints"][0][0]) < lag_threshold:
                self.logger.debug(
                    f"consumer group {msk_consumer_group} has an up-to-dateness of {data[0]['datapoints'][0][0]} which is less than the threshold of {lag_threshold}"
                )
                self._is_successful = False
                return

        self._is_successful = True


class ElasticSearchIngest(Check):
    _description = "Data is being ingested into NWT elasticsearch effectively"

    def check(self):
        pass


class NwtPublicWebUis(Check):
    _description = (
        "I can load the Kibana and Grafana NWT Web UIs via the NWT public DNS"
    )

    def check(self):
        self.logger.debug(f"Check: {self._description}")
        urls = {
            f"https://kibana.{self._sts.account_name}.telemetry.tax.service.gov.uk": 200,
            f"https://grafana.{self._sts.account_name}.telemetry.tax.service.gov.uk": 200,
        }

        try:
            for url, status_code in urls.items():
                r = requests.get(url)
                self.logger.debug(
                    f"URL: {url}, status code: {r.status_code}, expected {status_code}"
                )
                if r.status_code != status_code:
                    self._is_successful = False
                    break
                else:
                    self._is_successful = True
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return


class WebopsPublicWebUis(Check):
    _description = "I can load the Webops Kibana and Grafana Web UIs via the Webops tools proxy public DNS"

    def check(self):
        self._sts = Sts()

        account_name = str(self._sts.account_name)
        starts_with_mdtp = account_name.startswith("mdtp-")

        if starts_with_mdtp is True:
            account_name = account_name.replace("mdtp-", "")
        elif starts_with_mdtp is False:
            self._is_successful = False
            return

        urls = {
            f"https://kibana.tools.{account_name}.tax.service.gov.uk": 401,
            f"https://grafana.tools.{account_name}.tax.service.gov.uk": 200,
        }

        try:
            for url, status_code in urls.items():
                r = requests.get(url)
                self.logger.debug(
                    f"URL: {url}, status code: {r.status_code}, expected {status_code}"
                )
                if r.status_code != status_code:
                    self._is_successful = False
                    return
                else:
                    self._is_successful = True
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return
