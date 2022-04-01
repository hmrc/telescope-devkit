import boto3

from telemetry.telescope_devkit.cli import get_console


class Msk(object):
    def __init__(self):
        self._client = boto3.client("kafka")

    @property
    def default_cluster_arn(self):
        return self._client.list_clusters()["ClusterInfoList"][0]["ClusterArn"]

    def get_cluster_info(self):
        return self._client.describe_cluster(ClusterArn=self.default_cluster_arn)[
            "ClusterInfo"
        ]

    def get_brokers(self):
        brokers = {}
        response = self._client.list_nodes(
            ClusterArn=self.default_cluster_arn, MaxResults=100
        )
        for broker in response["NodeInfoList"]:
            broker_id = broker["BrokerNodeInfo"]["BrokerId"]
            brokers[broker_id] = broker

        while "NextToken" in response:
            response = self._client.list_nodes(
                ClusterArn=self.default_cluster_arn,
                MaxResults=100,
                NextToken=response["NextToken"],
            )
            for broker in response["NodeInfoList"]:
                broker_id = broker["BrokerNodeInfo"]["BrokerId"]
                brokers[broker_id] = broker

        return dict(sorted(brokers.items()))

    def get_bootstrap_servers(self):
        response = self._client.get_bootstrap_brokers(
            ClusterArn=self.default_cluster_arn
        )
        del response["ResponseMetadata"]
        return response

    def get_current_configuration(self):
        cluster_info = self.get_cluster_info()
        configuration_arn = cluster_info["CurrentBrokerSoftwareInfo"][
            "ConfigurationArn"
        ]
        configuration_revision = cluster_info["CurrentBrokerSoftwareInfo"][
            "ConfigurationRevision"
        ]

        response = self._client.describe_configuration_revision(
            Arn=configuration_arn, Revision=configuration_revision
        )
        del response["ResponseMetadata"]
        server_properties = {
            p.split("=")[0]: p.split(" = ")[1]
            for p in response["ServerProperties"].decode().splitlines()
        }
        response["ServerProperties"] = server_properties
        return response


class MskCli(object):
    def __init__(self):
        self._console = get_console()
        self._msk = Msk()

    def cluster(self):
        """Describes the MSK cluster"""
        self._console.print(self._msk.get_cluster_info())

    def bootstrap_servers(self):
        """Displays a list of brokers that a client application can use to bootstrap."""
        self._console.print(self._msk.get_bootstrap_servers())

    def brokers(self):
        """Returns a list of the broker nodes in the cluster."""
        self._console.print(self._msk.get_brokers())

    def configuration(self):
        """Displays the current cluster configuration"""
        self._console.print(self._msk.get_current_configuration())
