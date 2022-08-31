import os
import shlex
from typing import List, TextIO

from .._logging import get_logger


class BashScriptBuilder:
    """
    Builder pattern style bash script generator.

    Provides some convenience methods for common operations like, e.g., exporting an environment variable.
    """

    def __init__(self, path: str):
        self._path = path

        self._logger = get_logger("scriptgen")

        # initial value
        self._lines = [
            "#! /bin/bash",
            "",
            "# make sure to quit on errors in subcommands",
            "set -e",
            "set -o pipefail",
            "",
            "# if $VERBOSE is set to a value, print all commands (useful for debugging)",
            '[[ "$VERBOSE" != "" ]] && set -x',
            "",
        ]

    def export_env_var(self, name: str, value: str, raw: bool = False):
        name = shlex.quote(name)

        if not raw:
            value = shlex.quote(value)

        self.add_line("{}={}".format(name, value))
        self.add_line("export {}".format(name, value))

        return self

    def export_env_vars(self, variables: dict = None, raw: bool = False):
        for env_var, value in dict(variables).items():
            self.export_env_var(env_var, value, raw=raw)

        self.add_line()

        return self

    def add_lines(self, lines: List[str]):
        self._lines += lines

        return self

    def add_line(self, line: str = ""):
        self._lines.append(line)

        return self

    def build_string(self):
        # we want to force a blank line at the end, therefore we add an empty line
        rv = "\n".join(self._lines)

        if not rv.endswith("\n"):
            rv += "\n"

        return rv

    def build_file(self):
        with open(self._path, "w") as f:
            f.write(self.build_string())

        # shell scripts are supposed to be executable
        os.chmod(self._path, 0o755)


class ProjectAwareBashScriptBuilder(BashScriptBuilder):
    """
    Builder pattern style bash script generator. Used to generate build scripts in the build dir which export a common
    set of variables. This allows all scripts to be run independently of the main build script.
    """

    def __init__(self, path: str, project_root_dir: str, build_dir: str):
        super().__init__(path)

        # export PROJECT_ROOT and BUILD_DIR so they can be used by scripts etc.
        # convenience feature
        self.add_line("# convenience variables, may be used in config file")
        self.export_env_var("PROJECT_ROOT", project_root_dir)
        self.export_env_var("BUILD_DIR", build_dir)
        self.add_line()
