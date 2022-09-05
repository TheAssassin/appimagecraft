import os
import shutil

from . import ValidatorBase
from .exceptions import ValidationError

from subprocess import CalledProcessError, check_call


class ShellCheckValidator(ValidatorBase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _find_shellcheck():
        shellcheck_env = os.environ.get("SHELLCHECK", None)

        if shellcheck_env:
            return shellcheck_env

        return shutil.which("shellcheck")

    @staticmethod
    def is_available() -> bool:
        return bool(ShellCheckValidator._find_shellcheck())

    @staticmethod
    def supported_file_types():
        return ["*.sh", "*.bash"]

    def validate(self, path: str):
        shellcheck_path = self._find_shellcheck()

        if not shellcheck_path:
            raise ValidationError("could not find shellcheck")

        try:
            # SC2116 can be ignored safely, it's just about a "useless echo", but we want to test the version_cmd
            # feature with an echo call
            check_call([shellcheck_path, "-e", "SC2116", "-e", "SC1091", "-x", path], cwd=os.path.dirname(path))
        except CalledProcessError:
            raise ValidationError("failed to run shellcheck")
