import json
import logging
import shlex
import subprocess

import requests
from botocore.exceptions import ClientError
from rich.prompt import Prompt

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.ec2 import Ec2
from telemetry.telescope_devkit.logger import create_file_logger, get_file_logger
from telemetry.telescope_devkit.grafana import Grafana
from telemetry.telescope_devkit.sts import Sts, get_account_name


def create_migration_checklist_logger():
    account_name = Sts().account_name
    filename = f"{account_name}-migration-checklist.log"
    file_logger = create_file_logger(name="migration", filename=filename)
    get_console().print(
        f"* Check activity is being logged to [blue]log/{account_name}-migration-checklist.log[/blue]"
    )

    return file_logger


def get_migration_checklist_logger():
    return get_file_logger("migration")


class NotImplementedException(Exception):
    pass


class Check(object):
    _description = None
    _is_successful = None
    _requires_manual_intervention = False
    _console = get_console()
    _sts = None
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
            self._logger = get_migration_checklist_logger()
        return self._logger

    @property
    def sts(self):
        if self._sts is None:
            self._sts = Sts()
        return self._sts


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
        self.logger.info(f"Check: {self._description}")

        ec2 = Ec2()
        instance = ec2.get_instance_by_name(name="telemetry", enable_wildcard=False)
        if not instance:
            self.logger.debug(
                "There are no ECS telemetry running instances in this environment"
            )
            self._is_successful = False
            return

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


class KafkaConsumption(Check):
    _description = "Kafka consumption looks correct"

    def check(self):
        self.logger.info(f"Check: {self._description}")

        try:
            grafana = Grafana(
                hostname=f"grafana.{self.sts.account_name}.telemetry.tax.service.gov.uk"
            )
        except ClientError as e:
            self.logger.debug(e)
            self._is_successful = False
            return

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
        lag_threshold = 90
        for msk_consumer_group in msk_consumer_groups:
            metric_query = f"alias(offset(scale(keepLastValue(divideSeries(telemetry.telescope.msk.{msk_consumer_group}.sum-lag%2Ctelemetry.telescope.msk.{msk_consumer_group}.sum-range)%2C%2060)%2C%20-100)%2C%20100)%2C%20'Offset')&from=-{msk_log_retention_period}&until=now&format=json&maxDataPoints=1"
            data = grafana.get_metric_value(metric_query=metric_query)
            currentness_percentage = round(data[0]["datapoints"][0][0], 2)
            if currentness_percentage < lag_threshold:
                self.logger.debug(
                    f"consumer group {msk_consumer_group} has an up-to-dateness of {currentness_percentage}% which is less than the threshold of {lag_threshold}%"
                )
                self._is_successful = False
                return

        self._is_successful = True


class ElasticSearchIngest(Check):
    _description = "Data is being ingested into NWT elasticsearch effectively"
    _indexing_rate_period = "15min"
    _rate_diff_threshold = 10  # percentage difference

    def _get_indexing_rate_from_webops(self):
        account_name = str(self.sts.account_name).replace("mdtp-", "")
        grafana = Grafana(
            hostname=f"grafana.tools.{account_name}.tax.service.gov.uk",
            ssm_path="/telemetry/secrets/grafana/webops_migration_api_key",
        )
        metric_query = f"averageSeries(sumSeries(removeEmptySeries(perSecond(collectd.elasticsearch-data*.es-default.gauge-index.docs.count))))&from=-{self._indexing_rate_period}&until=now&format=json&maxDataPoints=1"
        data = grafana.get_metric_value(metric_query=metric_query)
        return round(float(data[0]["datapoints"][0][0]), 2)

    def _get_indexing_rate_from_tnt(self):
        account_name = str(self.sts.account_name).replace("mdtp-", "")
        grafana = Grafana(
            hostname="grafana.internal-telemetry.telemetry.tax.service.gov.uk",
            ssm_path="/telemetry/secrets/grafana/tnt_migration_api_key",
        )
        # get environment cidr A&B
        ec2 = Ec2()
        instance = ec2.get_instance_by_name(
            name="elasticsearch-query", enable_wildcard=False
        )
        ip_blocks = instance["PrivateIpAddress"].split(".")
        ip_filter = f"ip-{ip_blocks[0]}-{ip_blocks[1]}-"

        metric_query = f"averageSeries(sumSeries(removeEmptySeries(perSecond(collectd.elasticsearch-data*{ip_filter}*.es-default.gauge-index.docs.count))))&from=-{self._indexing_rate_period}&until=now&format=json&maxDataPoints=1"
        data = grafana.get_metric_value(metric_query=metric_query)
        return round(float(data[0]["datapoints"][0][0]), 2)

    def check(self):
        self.logger.info(f"Check: {self._description}")

        try:
            webops_indexing_rate = self._get_indexing_rate_from_webops()
            tnt_indexing_rate = self._get_indexing_rate_from_tnt()
        except ClientError as e:
            self.logger.debug(e)
            self._is_successful = False
            return

        rate_difference = round(
            (abs(webops_indexing_rate - tnt_indexing_rate) / webops_indexing_rate)
            * 100,
            2,
        )
        if rate_difference < self._rate_diff_threshold:
            self._is_successful = True
        else:
            self.logger.debug(
                "The difference between elasticsearch ingest in webops compared to NWT is above threshold"
            )
            self.logger.debug(f"Indexing rate in webops is {webops_indexing_rate}")
            self.logger.debug(f"Indexing rate in NWT is {tnt_indexing_rate}")
            self.logger.debug(f"Indexing rate difference is {rate_difference}%")
            self._is_successful = False


class NwtPublicWebUis(Check):
    _description = (
        "I can load the Kibana and Grafana NWT Web UIs via the NWT public DNS"
    )

    def check(self):
        self.logger.info(f"Check: {self._description}")
        urls = {
            f"https://kibana.{self.sts.account_name}.telemetry.tax.service.gov.uk": 200,
            f"https://grafana.{self.sts.account_name}.telemetry.tax.service.gov.uk": 200,
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
        self.logger.info(f"Check: {self._description}")

        account_name = str(self.sts.account_name)
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


class LogsDataIsValid(Check):
    _description = "Logs data in NWT is valid"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class MetricsDataIsValid(Check):
    _description = "Metrics data in NWT is valid"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class RelevantAlertsAreRunningInWebops(Check):
    _description = "Relevant alerts are still running in webops"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class InitialAlertsAreRunningInNwt(Check):
    _description = "Initial NWT alert(s) is running in NWT"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class NwtPublicWebUisRedirectFromWebops(Check):
    _description = "I am successfully redirected to NWT Kibana & Grafana when hitting the webops tools URLs"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class RelevantAlertsAreRunningInNwt(Check):
    _description = "Relevant alerts are now running in NWT"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class WebopsPublicWebUisNotRunning(Check):
    _description = "The following are no longer running in webops: Clickhouse, Elasticsearch, Kibana, Grafana"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()
