import json
import os

import boto3
import inspect

from telemetry.telescope_devkit import APP_NAME
from telemetry.telescope_devkit.filesystem import get_repo_path
from telemetry.telescope_devkit.cli import get_console
from telemetry.telescope_devkit.sts import load_aws_accounts
from rich.prompt import Prompt

# class MultiAccount(object):
#     def __init__(self):
#         try:
#             self._sts = Sts()
#         except ValueError as e:
#             raise Exception(f"{e}\nAre you running {APP_NAME} in an AWS profile?")
#         self.aws_accounts = load_aws_accounts()

#     def assume_role(self, role, mfa_code) -> str:
#         response = self._sts.assume_role(role, mfa_code)

#     def get_caller_identity(self, sts_client) -> str:
#         return Sts(sts_client).account_name

class MultiAccountProxy(object):
    
    def __init__(self, target):
        self._console = get_console()
        self._console.print(f"Proxying to {target}")
        self._session = None

        functions = inspect.getmembers(target, predicate=inspect.isfunction)
        
        for name, function in functions:
            if not name.startswith("_"):
                self._console.print(f"Proxying to function {name}, {function}")
                setattr(self, name, self._invoke_wrapper(target, function))
            else:
                self._console.print(f"Ignoring private function {name}")

    def _invoke_wrapper(self, target, function):
        def invoke():
            self._console.print(f'initialising {target}')

            for account in ["telemetry-mdtp-integration", "telemetry-mdtp-development"]:
                session = boto3.Session(profile_name=f"{account}-RoleTelemetryEngineer")
                target.__init__(target, session)
                self._console.print(f'invoking {function} on {target}')
                response = function(target)
                self._console.print(response)

        return invoke

class MultiAccountCli(object):
    def __init__(self, commands):
        self._console = get_console()
        # self._multiaccount = MultiAccount()
        # self.logs = commands["logs"]
        self.proxy_commands(commands)

    def proxy_commands(self, commands):
        for index, key in enumerate(commands):
            val = commands[key]
            is_dict = type(val) is dict
            self._console.print(f"i {index} k {key}, v {val}, is_dict {is_dict}")
            
            if is_dict:
                self._console.print('ignoring dict for now')
            else:
                setattr(self, key, MultiAccountProxy(commands[key]))

    # def command_proxy(self):
    #     print('proxy')

    # def cf_create_change_set(self) -> None:
    #     self._console.print("[bold green]Creating change sets...")
    
    #     # print(self._multiaccount.aws_accounts)
    #     # for role in ["arn:aws:iam::634456480543:role/RoleChangeSetCreator", "arn:aws:iam::634456480543:role/RoleChangeSetCreator"]:
    #     # for account in ["072254306672", "421310561273"]:
    #     for account in ["telemetry-internal-integration", "telemetry-internal-development"]:
    #         # role = f"arn:aws:iam::{account}:role/RoleChangeSetCreator"
    #         session = boto3.Session(profile_name=f"{account}-RoleChangeSetCreator")
    #         sts_client = session.client('sts')

    #         # mfa_code = Prompt.ask(
    #         #     "Please enter an MFA code"
    #         # )
    #         # print (mfa_code)
    #         response = self._multiaccount.get_caller_identity(sts_client)
    #         account = response["Account"]
    #         arn = response["Arn"]
    #         self._console.print(f"Currently running in {account} as {arn}")
