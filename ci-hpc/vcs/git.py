#!/bin/python3
# author: Jan Hybs

import os
import sys
import shutil
import subprocess
from proc.execution import create_execute_command
from utils.logging import logger


class Git(object):
    """
    :type git: structures.project_step_git.ProjectStepGit
    """
    def __init__(self, git):
        self.git = git
        self.dir = os.path.abspath(os.path.join(os.getcwd(), self.git.repo))
        self.execute = create_execute_command(
            logger_method=logger.debug,
            stdout=subprocess.DEVNULL,
        )

    def clone(self):
        if self.git.remove_before_checkout:
            shutil.rmtree(self.dir, ignore_errors=True)

        if os.path.exists(self.dir):
            # print('Directory not empty', self.dir, '(git clone skipped)')
            return

        self.execute('git clone', self.git.url, self.dir).wait()

    def checkout(self):
        branch = self.git.branch
        commit = self.git.commit

        if branch:
            branch = branch.replace('origin/', '')

        logger.info('Git checkout repo={self.git.repo} to branch={self.git.branch}, commit={self.git.commit}'.format(self=self))
        self.execute("git config core.pager", "", dir=self.dir) # turn of less pager
        self.execute('pwd', dir=self.dir).wait()
        self.execute('git branch -vv', dir=self.dir).wait()
        self.execute('git fetch', dir=self.dir).wait()

        if branch:
            # just in case set remote upstream branch
            # then forcefully checkout to branch
            # and pull the latest changes
            self.execute('git branch --set-upstream-to=origin/%s %s' % (branch, branch), dir=self.dir).wait()
            self.execute('git checkout -f', branch, dir=self.dir).wait()
            self.execute('git pull', dir=self.dir).wait()

        if commit:
            # if there is a commit specified, we forcefully checkout it out
            head = subprocess.check_output('git rev-parse HEAD'.split(), cwd=self.dir).decode()
            if head != commit:
                self.execute('git checkout -f', commit, dir=self.dir).wait()
                # create new local branch with given name (if branch is specified)
                # so if someone asks on which branch we are, answer won't be 'detached HEAD'
                if branch:
                    self.execute('git branch -d', branch, dir=self.dir).wait()
                    self.execute('git checkout -b', branch, dir=self.dir).wait()

    def info(self):
        logger.debug('Repository currently at:')
        self.execute('git branch -vv', dir=self.dir).wait()
        self.execute('git log -n 10 --graph', '--pretty=format:%h %ar %aN%d %s', dir=self.dir).wait()
