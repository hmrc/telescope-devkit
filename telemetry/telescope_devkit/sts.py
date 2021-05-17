import json
import os

import boto3

from telemetry.telescope_devkit import APP_NAME
from telemetry.telescope_devkit.filesystem import get_repo_path


class Sts(object):
    def __init__(self):
        try:
            self._sts = boto3.client('sts')
        except ValueError as e:
            raise Exception(f"{e}\nAre you running {APP_NAME} in an AWS profile?")
        self.aws_accounts = load_aws_accounts()

    @property
    def account(self) -> str:
        return self._sts.get_caller_identity()['Account']

    @property
    def user_id(self) -> str:
        return self._sts.get_caller_identity()['UserId']

    @property
    def is_webops_account(self) -> bool:
        return self.aws_accounts[self.account].startswith('webops-')

    @property
    def account_name(self) -> str:
        return self.aws_accounts[self.account]


def load_aws_accounts() -> dict:
    with open(os.path.join(get_repo_path(), "data/aws-accounts.json")) as json_file:
        data = json.load(json_file)
        return {v: k for k, v in data.items()}



def get_account_name() -> str:
    return Sts().account_name