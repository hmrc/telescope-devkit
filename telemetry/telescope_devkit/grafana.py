import time
from typing import List

import boto3
import requests


class Grafana:
    def __init__(
        self, hostname: str = "localhost", port: int = 443, scheme: str = "https", ssm_path: str = "/telemetry/secrets/grafana/migration_api_key"
    ):
        api_key = self._get_api_key(ssm_path)
        self.default_headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        self.base_url = f"{scheme}://{hostname}:{port}"

    def has_metric(self, metric_path: str) -> bool:
        datasource_id = self._get_datasource_id("carbonapi-clickhouse")

        url = f"{self.base_url}/api/datasources/proxy/{datasource_id}/metrics/find"
        headers = self.default_headers
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = f"query={metric_path}"

        has_metric = False
        timeout = 10  # seconds

        while timeout >= 0:
            response = requests.post(url, data=data, headers=headers)

            if response.status_code != 200:
                raise Exception(
                    f"ERROR! has_metric received unexpected response code {response.status_code}, response: {response.content}"
                )

            json = response.json()
            has_metric = json and json[0]["id"] == metric_path

            timeout -= 1
            time.sleep(1)

            if has_metric:
                break

        if has_metric:
            print(f"✅ Metric '{metric_path}' was found in Grafana.")
        else:
            print(f"❌ Metric '{metric_path}' not found in Grafana.")

        return has_metric

    def get_metric_value(self, metric_query: str) -> List:
        datasource_id = self._get_datasource_id("carbonapi-clickhouse")

        url = f"{self.base_url}/api/datasources/proxy/{datasource_id}/render?format=json"
        headers = self.default_headers
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        data = f"target={metric_query}"

        response = requests.post(url, data=data, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"ERROR! get_metric_value received unexpected response code {response.status_code}, response: {response.content}"
            )

        return response.json()

    def _get_datasource_id(self, name: str) -> int:
        url = f"{self.base_url}/api/datasources/name/{name}"
        headers = self.default_headers
        headers["Content-Type"] = "application/json"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"ERROR! _get_datasource_id received unexpected response code {response.status_code}, response: {response.content}"
            )

        return response.json()["id"]

    def _get_api_key(self, ssm_path: str) -> str:
        ssm = boto3.client("ssm")
        parameter = ssm.get_parameter(
            Name=ssm_path, WithDecryption=True
        )
        api_key = parameter["Parameter"]["Value"]

        return api_key
