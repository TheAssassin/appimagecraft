import os

from . import ValidatorBase
from .exceptions import ValidationError

from subprocess import CalledProcessError, check_call


class ShellCheckValidator(ValidatorBase):
    def __init__(self):
        super().__init__()

    @staticmethod
    def is_available() -> bool:
        try:
            with open(os.devnull, "w") as devnull:
                check_call(["command", "-v", "shellcheck"], stderr=devnull, stdout=devnull, shell=True)
        except CalledProcessError:
            return False
        else:
            return True

    @staticmethod
    def supported_file_types():
        return ["*.sh", "*.bash"]

    def validate(self, path: str):
        try:
            # SC2116 can be ignored safely, it's just about a "useless echo", but we want to test the version_cmd
            # feature with an echo call
            check_call(["shellcheck", "-e", "SC2116", "-x", path], cwd=os.path.dirname(path))
        except CalledProcessError:
            raise ValidationError("failed to run shellcheck")
