import json
import os

import boto3
from boto3.session import Session

from telemetry.telescope_devkit import APP_NAME
from telemetry.telescope_devkit.filesystem import get_repo_path


class Sts(object):
    def __init__(self):
        try:
            self._sts = boto3.client("sts")
        except ValueError as e:
            raise Exception(f"{e}\nAre you running {APP_NAME} in an AWS profile?")
        self.aws_accounts = load_aws_accounts()

    @property
    def account(self) -> str:
        return self._sts.get_caller_identity()["Account"]

    @property
    def account_name(self) -> str:
        return self.aws_accounts[self.account]

    @property
    def user_id(self) -> str:
        return self._sts.get_caller_identity()["UserId"]

    @property
    def is_mdtp_account(self) -> bool:
        return self.aws_accounts[self.account].startswith("mdtp-")

    @property
    def is_webops_account(self) -> bool:
        return self.aws_accounts[self.account].startswith("webops-")

    @property
    def webops_account_name(self) -> str or None:
        return (
            str(self.account_name).replace("mdtp-", "")
            if self.is_mdtp_account
            else None
        )

    def start_webops_telemetry_engineer_role_session(self) -> Session:
        profile = f"webops-{self.webops_account_name}-engineer/RoleTelemetryEngineer"

        return Session(profile_name=profile)


def load_aws_accounts() -> dict:
    with open(os.path.join(get_repo_path(), "data/aws-accounts.json")) as json_file:
        data = json.load(json_file)
        return {v: k for k, v in data.items()}


def get_account_name() -> str:
    return Sts().account_name
