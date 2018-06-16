import os
import sys


class TempFile(object):

    def __init__(self, path, verbose=False):
        self.path = path
        self.lines = []
        self.verbose = verbose

    def write_shebang(self, interpreter='/bin/bash'):
        self.write('#!/bin/bash')
        self.write('### AUTOGENERATED DO NOT EDIT ###')
        if self.verbose:
            self.write('set -x')
        self.write('# ----------------------------- #')
        self.write('')

    def read(self):
        with open(self.path, 'r') as fp:
            return fp.read()

    def write(self, s='', new_line=True):
        self.lines.append(s)
        if new_line:
            self.lines.append('\n')

    def __enter__(self):
        self.lines = []
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.path, 'w') as fp:
            for s in self.lines:
                fp.write(s)
        os.chmod(self.path, 0o755)

        return False
