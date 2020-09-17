import os
import shlex
from typing import List, TextIO

from .._logging import get_logger


class BashScriptGenerator:
    def __init__(self, path):
        self._path = path

        self._lines = []

        self._logger = get_logger("scriptgen")

    def export_env_var(self, name: str, value: str, raw: bool = False):
        name = shlex.quote(name)

        if not raw:
            value= shlex.quote(value)

        self.add_line("export {}={}".format(name, value))

    def export_env_vars(self, variables: dict = None, raw: bool = False):
        for env_var, value in dict(variables).items():
            self.export_env_var(env_var, value, raw=raw)

        self.add_line()

    def add_lines(self, lines: List[str]):
        self._lines += lines

        return self

    def add_line(self, line: str = ""):
        self._lines.append(line)

        return self

    @staticmethod
    def _write_lines(file: TextIO, lines):
        file.writelines((str(i) + "\n" for i in lines))

    def _write_header(self, file: TextIO):
        self._write_lines(file, [
            "#! /bin/bash",
            "",
            "# make sure to quit on errors in subcommands",
            "set -e",
            "",
        ])

    def build_file(self):
        with open(self._path, "w") as f:
            self._write_header(f)
            self._write_lines(f, self._lines)

        # shell scripts are supposed to be executable
        os.chmod(self._path, 0o755)
