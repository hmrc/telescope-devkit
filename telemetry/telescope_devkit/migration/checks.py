import datetime
import json
import re
import shlex
import subprocess
from json.decoder import JSONDecodeError
from subprocess import PIPE
from subprocess import Popen

import requests
from botocore.exceptions import ClientError
from rich.prompt import Prompt

from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.codebuild import Codebuild
from telemetry.telescope_devkit.ec2 import Ec2
from telemetry.telescope_devkit.grafana import Grafana
from telemetry.telescope_devkit.logger import create_file_logger
from telemetry.telescope_devkit.logger import get_file_logger
from telemetry.telescope_devkit.sts import get_account_name
from telemetry.telescope_devkit.sts import Sts


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


def get_epoch_start_and_end_times(from_minutes_ago=15, to_minutes_ago=10):
    now = datetime.datetime.now()
    from_timestamp = int(
        (now - datetime.timedelta(minutes=from_minutes_ago)).timestamp()
    )
    to_timestamp = int((now - datetime.timedelta(minutes=to_minutes_ago)).timestamp())
    return from_timestamp, to_timestamp


def get_percentage_diff(previous, current):
    try:
        percentage = abs(previous - current) / max(previous, current) * 100
    except ZeroDivisionError:
        percentage = float("inf")
    return percentage


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
    _description = "Terraform CodeBuild project is green"

    def check(self):
        self.logger.info(f"Check: {self._description}")
        codebuild = Codebuild()
        session = Sts().start_internal_base_engineer_role_session()

        self._is_successful = False

        latest_build_id = codebuild.get_latest_terraform_build_id(
            f"build-telemetry-{get_account_name()}-terraform", session
        )
        self.logger.debug(f"Latest Terraform build identifier = {latest_build_id}")
        latest_build_status = codebuild.get_terraform_build_status(
            latest_build_id, session
        )
        self.logger.debug(f"Latest Terraform build status = {latest_build_status}")

        if latest_build_status == "SUCCEEDED":
            self._is_successful = True
            return


class EcsStatusChecks(Check):
    _description = "ECS Status Checks are green"

    def check(self):
        self.logger.info(f"Check: {self._description}")

        ec2 = Ec2()
        instance = ec2.get_instance_by_name(name="telemetry-ecs", enable_wildcard=False)
        if not instance:
            self.logger.debug(
                "There are no ECS telemetry running instances in this environment"
            )
            self._is_successful = False
            return

        # get the ecs status check result
        cmd = f'ssh {instance.private_ip_address} curl http://ecs-status-checks.telemetry.internal:5000/test -s -o /dev/null -I -w "%{{http_code}}"'
        completed_process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        return_code = completed_process.stdout.decode("utf-8")
        if return_code == "200":
            self._is_successful = True
            return

        self._is_successful = False
        # return to the user the details ecs status check results
        self.logger.debug(f"ECS Status Checks returned status code {return_code}")
        self.logger.debug("detailed result of ecs-status-checks:")
        cmd = f"ssh {instance.private_ip_address} curl http://ecs-status-checks.telemetry.internal:5000 -s"
        completed_process = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
        try:
            response = json.loads(completed_process.stdout)
            self.logger.debug(json.dumps(response, indent=4))
        except JSONDecodeError as e:
            self.logger.debug(e)


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
        metric_query = "aliasByNode(telemetry.telescope.msk.logs.partition_*.offset%2C%204)&from=-5min&until=now&format=json&maxDataPoints=1"
        try:
            data = grafana.get_metric_value(metric_query=metric_query)
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return

        for partition in data:
            if int(partition["datapoints"][0][0]) < 0:
                self.logger.debug(
                    f"{partition['target']} has an offset of {partition['datapoints'][0][0]} which is an error code"
                )
                self._is_successful = False
                return

        # Validate that all consumers are up-to-date
        msk_consumer_groups = ["logs"]
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
        if not data:
            raise Exception(
                f"No datapoints available for metrics query '{metric_query}'"
            )

        return round(float(data[0]["datapoints"][0][0]), 2)

    def _get_indexing_rate_from_tnt(self):
        grafana = Grafana(
            hostname="grafana.internal-telemetry.telemetry.tax.service.gov.uk",
            ssm_path="/telemetry/secrets/grafana/tnt_migration_api_key",
        )
        # get environment cidr A&B
        ec2 = Ec2()
        instance = ec2.get_instance_by_name(
            name="elasticsearch-query", enable_wildcard=False
        )
        ip_blocks = instance.private_ip_address.split(".")
        ip_filter = f"ip-{ip_blocks[0]}-{ip_blocks[1]}-"

        metric_query = f"averageSeries(sumSeries(removeEmptySeries(perSecond(collectd.elasticsearch-data*{ip_filter}*.es-default.gauge-index.docs.count))))&from=-{self._indexing_rate_period}&until=now&format=json&maxDataPoints=1"
        data = grafana.get_metric_value(metric_query=metric_query)
        if not data:
            raise Exception(
                f"No datapoints available for metrics query '{metric_query}'"
            )

        return round(float(data[0]["datapoints"][0][0]), 2)

    def _get_indexing_rate_from_mdtp(self):
        account_name = str(self.sts.account_name)
        grafana = Grafana(
            hostname=f"grafana.{account_name}.telemetry.tax.service.gov.uk",
            ssm_path="/telemetry/secrets/grafana/migration_api_key",
        )
        # get environment cidr A&B
        ec2 = Ec2()
        instance = ec2.get_instance_by_name(
            name="elasticsearch-query", enable_wildcard=False
        )
        ip_blocks = instance.private_ip_address.split(".")
        ip_filter = f"ip-{ip_blocks[0]}-{ip_blocks[1]}-"

        metric_query = f"averageSeries(sumSeries(removeEmptySeries(perSecond(collectd.elasticsearch-data*{ip_filter}*.es-default.gauge-index.docs.count))))&from=-{self._indexing_rate_period}&until=now&format=json&maxDataPoints=1"
        data = grafana.get_metric_value(metric_query=metric_query)
        if not data:
            raise Exception(
                f"No datapoints available for metrics query '{metric_query}'"
            )

        return round(float(data[0]["datapoints"][0][0]), 2)

    def check(self):
        self.logger.info(f"Check: {self._description}")

        try:
            webops_indexing_rate = self._get_indexing_rate_from_webops()
            # tnt_indexing_rate = self._get_indexing_rate_from_tnt()
            mdtp_indexing_rate = self._get_indexing_rate_from_mdtp()
        except ClientError as e:
            self.logger.debug(e)
            self._is_successful = False
            return
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return

        rate_difference = round(
            (abs(webops_indexing_rate - mdtp_indexing_rate) / webops_indexing_rate)
            * 100,
            2,
        )

        self.logger.debug(f"Indexing rate in WebOps is {webops_indexing_rate}")
        self.logger.debug(f"Indexing rate in MDTP is {mdtp_indexing_rate}")
        self.logger.debug(f"Indexing rate difference is {rate_difference}%")

        if rate_difference < self._rate_diff_threshold:
            self._is_successful = True
        else:
            self.logger.debug(
                "The difference between elasticsearch ingest in webops compared to NWT is above threshold"
            )
            self.logger.debug(f"Indexing rate in WebOps is {webops_indexing_rate}")
            # self.logger.debug(f"Indexing rate in NWT is {tnt_indexing_rate}")
            self.logger.debug(f"Indexing rate in MDTP is {mdtp_indexing_rate}")
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
    _description = "I can load the Webops Kibana and Grafana Web UIs via the WebOps tools proxy public DNS"

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


class ClickhouseMetricsChecks(Check):
    _description = "Metrics data ingested in NWT matches WebOps"
    _requires_manual_intervention = False

    def check(self):
        self.logger.info(f"Check: {self._description}")

        start_time, end_time = get_epoch_start_and_end_times()
        self.logger.debug(f"Start Time: {start_time}")
        self.logger.debug(f"End Time: {end_time}")

        nwt_account_name = str(self.sts.account_name)
        webops_account_name = str(self.sts.account_name).replace("mdtp-", "webops-")
        clickhouse_query = (
            f'echo "SELECT COUNT(*) FROM graphite.graphite_distributed WHERE Time > {start_time} and '
            f'Time < {end_time}" | clickhouse client '
        )

        # Get metric count from NWT environment
        nwt_ec2 = Ec2()
        nwt_metric_count = self._get_metric_ingest_count(
            nwt_ec2, clickhouse_query, nwt_account_name
        )
        if nwt_metric_count is None:
            self._is_successful = False
            return

        # Get metric count from WebOps environment
        webops_ec2 = Ec2(self.sts.start_webops_telemetry_engineer_role_session())
        webops_metric_count = self._get_metric_ingest_count(
            webops_ec2, clickhouse_query, webops_account_name
        )
        if webops_metric_count is None:
            self._is_successful = False
            return

        try:
            percentage_difference = get_percentage_diff(
                nwt_metric_count, webops_metric_count
            )
            self.logger.debug(f"Percentage difference: {percentage_difference}")

            if percentage_difference <= 3:
                self.logger.debug("Metrics ingested within 3%")
                self._is_successful = True
            else:
                self.logger.debug("Metrics ingested greater than 3%")
                self._is_successful = False
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return

    def _get_metric_ingest_count(self, ec2_client, clickhouse_query, environment_name):
        try:
            instance = ec2_client.get_instance_by_name(
                name="clickhouse-server-shard_1", enable_wildcard=False
            )
            if not instance:
                self.logger.debug(
                    f"There are no Clickhouse Shard 1 instances in {environment_name}"
                )
                return None

            self.logger.debug(
                f"Getting metrics from Clickhouse in {environment_name}: {instance.private_ip_address}"
            )
            stdout, stderr = Popen(
                ["ssh", instance.private_ip_address, clickhouse_query], stdout=PIPE
            ).communicate()
            return_value = int(stdout.decode("utf-8").strip())
            self.logger.debug(
                f"Ingested metric count for {environment_name}: {return_value}"
            )
            return return_value
        except Exception as e:
            self.logger.debug(e)
            return None


class ClickhouseSnapshotGeneration(Check):
    _description = "Clickhouse Data Volume Snapshots Taken"
    _requires_manual_intervention = False

    def check(self):
        self.logger.info(f"Generate: {self._description}")
        webops_account_name = str(self.sts.account_name).replace("mdtp-", "webops-")

        try:
            # Create snapshots in WebOps for both shards 1 & 2
            webops_ec2 = Ec2(self.sts.start_webops_telemetry_engineer_role_session())
            shard_1_snapshot = self._generate_snapshot(
                webops_ec2, webops_account_name, "shard_1"
            )
            if shard_1_snapshot is None:
                self._is_successful = False
                return

            shard_2_snapshot = self._generate_snapshot(
                webops_ec2, webops_account_name, "shard_2"
            )
            if shard_2_snapshot is None:
                self._is_successful = False
                return

            self.logger.debug(shard_1_snapshot.snapshot_id)
            self.logger.debug(shard_2_snapshot.snapshot_id)
            self._is_successful = True
        except Exception as e:
            self.logger.debug(e)
            self._is_successful = False
            return

    def _generate_snapshot(self, ec2_client, environment_name, shard):
        try:
            volume = ec2_client.get_volume_by_filter(
                filter_name="tag:Component", filter_value=f"clickhouse-server-{shard}"
            )
            if not volume:
                self.logger.debug(
                    f"There are no data volumes found for {shard} instances in {environment_name}"
                )
                return None

            self.logger.debug(
                f"Generating {shard} snapshot from Clickhouse in {environment_name}: "
                f"{volume.id} ({volume.size} GiB) -> {volume.state}"
            )

            snapshot = ec2_client.generate_snapshot(
                description=f"Manual snapshot taken for {shard}", volume_id=volume.id
            )

            if not snapshot:
                self.logger.debug(
                    f"Snapshot was unsuccessful for {shard} in {environment_name}"
                )
                return None

            return snapshot
        except Exception as e:
            self.logger.debug(e)
            return None


class MetricsDataIsValid(Check):
    _description = "Metrics data in NWT is valid"
    _requires_manual_intervention = False

    def check(self):
        self.logger.info(f"Check: {self._description}")

        from_minutes_ago = 15
        to_minutes_ago = 10
        from_timestamp, to_timestamp = get_epoch_start_and_end_times(
            from_minutes_ago, to_minutes_ago
        )

        max_data_points = from_minutes_ago - to_minutes_ago
        metric_query = f"alias(maximumAbove(group(averageSeriesWithWildcards(%7Bplay%2Cportal%7D.platform-status-frontend.*.heap.max%2C0%2C2)%2CaverageSeriesWithWildcards(%7Bplay%2Cportal%7D.platform-status-frontend.*.jvm.memory.heap.max%2C0%2C2))%2C0)%2C%20'Heap%20Max')&from={from_timestamp}&until={to_timestamp}&format=json&maxDataPoints={max_data_points}"
        self.logger.debug(f"Fetching data for graphite query: '{metric_query}'")

        try:
            nwt_datapoints = self._get_metric_values_from_nwt(metric_query)
            self.logger.debug(f"{self.sts.account_name} datapoints: {nwt_datapoints}")

            webops_datapoints = self._get_metric_values_from_webops(metric_query)
            webops_account_name = str(self.sts.account_name).replace("mdtp-", "webops-")
            self.logger.debug(f"{webops_account_name} datapoints: {webops_datapoints}")

            if nwt_datapoints == webops_datapoints:
                self.logger.debug("Datapoints match")
                self._is_successful = True
            else:
                self.logger.debug("Datapoints don't match")
                self._is_successful = False
        except ClientError as e:
            self.logger.debug(e)
            self._is_successful = False
            return

    def _get_metric_values_from_nwt(self, metric_query: str):
        grafana = Grafana(
            hostname=f"grafana.{self.sts.account_name}.telemetry.tax.service.gov.uk"
        )
        data = grafana.get_metric_value(metric_query=metric_query)

        return data[0]["datapoints"]

    def _get_metric_values_from_webops(self, metric_query: str):
        webops_account_name = str(self.sts.account_name).replace("mdtp-", "")
        grafana = Grafana(
            hostname=f"grafana.tools.{webops_account_name}.tax.service.gov.uk",
            ssm_path="/telemetry/secrets/grafana/webops_migration_api_key",
        )
        data = grafana.get_metric_value(metric_query=metric_query)

        return data[0]["datapoints"]


class SensuChecksAreRunningInWebops(Check):
    _description = "Sensu checks are still running in WebOps"
    _requires_manual_intervention = True

    def check_interactively(self):
        return self.launch_manual_intervention_prompt()


class NwtPublicWebUisRedirectFromWebops(Check):
    _description = "I am successfully redirected to NWT Kibana & Grafana when hitting the WebOps tools URLs"

    def check(self):
        self.logger.info(f"Check: {self._description}")
        self._is_successful = self._check_grafana() and self._check_kibana()

    def _check_grafana(self):
        grafana_url = (
            f"https://grafana.tools.{self.sts.webops_account_name}.tax.service.gov.uk"
        )
        try:
            grafana_major_version = "8"
            self.logger.debug(f"Fetching HTML content from {grafana_url}")
            r = requests.get(grafana_url)
            match = re.search(
                rf"Grafana v{grafana_major_version}\.\d+\.\d+", r.text, re.IGNORECASE
            )
            return match is not None
        except Exception as e:
            self.logger.debug(e)
            return False

    def _check_kibana(self):
        kibana_major_version = "7"
        kibana_url = (
            f"https://kibana.tools.{self.sts.webops_account_name}.tax.service.gov.uk"
        )
        try:
            self.logger.debug(f"Fetching HTML content from {kibana_url}")
            r = requests.get(kibana_url)
            match = re.search(
                rf"&quot;version&quot;:&quot;{kibana_major_version}\.\d+\.\d+&quot;",
                r.text,
                re.IGNORECASE,
            )
            return match is not None
        except Exception as e:
            self.logger.debug(e)
            return False


class WebopsEc2InstancesHaveBeenDecommissioned(Check):
    _description = "The following are no longer running in WebOps: ClickHouse, Elasticsearch-Data, Elasticsearch-Data-Warm, Elasticsearch-Query, Kibana, Grafana"
    _requires_manual_intervention = False

    def check(self):
        self.logger.info(f"Check: {self._description}")

        webops_ec2 = Ec2(self.sts.start_webops_telemetry_engineer_role_session())
        instance_names = [
            "clickhouse-server-shard_1",
            "clickhouse-server-shard_2",
            "elasticsearch-data",
            "elasticsearch-data-warm",
            "elasticsearch-query",
            "elasticsearch-kibana",
            "graphite-frontend",
        ]
        for instance_name in instance_names:
            instances = webops_ec2.get_instances_by_name(
                name=instance_name, enable_wildcard=False
            )
            instance_count = len(list(instances))
            self.logger.debug(
                f"There are {instance_count} {instance_name} instance(s) running in the {self.sts.webops_account_name} account"
            )
            if instance_count > 0:
                self._is_successful = False
                return

        self._is_successful = True
