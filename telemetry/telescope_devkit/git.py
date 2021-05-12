import logging
import os

from git import Repo
from telemetry.telescope_devkit.filesystem import get_repo_path

GIT_DEFAULT_MAIN_BRANCH_NAME = 'main'
GIT_DEFAULT_REMOTE_NAME = 'vitorbrandao'


class TelescopeDevkitGitRepo(object):
    def __init__(self, debug: bool = False):
        self.main_branch = GIT_DEFAULT_MAIN_BRANCH_NAME
        self.remote_name = GIT_DEFAULT_REMOTE_NAME
        if debug is True:
            logging.basicConfig(level=logging.DEBUG)
            os.putenv('GIT_PYTHON_TRACE', '1')
            os.environ['GIT_PYTHON_TRACE'] = '1'
        self.repo = Repo(get_repo_path())
        assert not self.repo.bare
        assert os.path.isdir(self.repo.working_tree_dir)

    @property
    def current_version(self) -> str:
        return self.repo.git.describe(always=True)

    @property
    def active_branch(self) -> str:
        return self.repo.active_branch

    def pull(self) -> None:
        if self.remote_name not in self.repo.remotes:
            raise TelescopeDevkitGitRepoException(f"No remote named '{self.remote_name}' was found.")
        remote = self.repo.remotes[self.remote_name]
        remote.pull()

    def update(self):
        if self.main_branch != self.repo.active_branch:
            raise TelescopeDevkitGitRepoException(f"Unable to update as the Git repo is not on the " +
                                                  f"'{self.main_branch}' branch. Current branch is '{self.repo.active_branch}'.")
        self.pull()


class TelescopeDevkitGitRepoException(Exception):
    pass
