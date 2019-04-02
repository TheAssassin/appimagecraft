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
                check_call(["which", "shellcheck"], stderr=devnull, stdout=devnull)
        except CalledProcessError:
            return False
        else:
            return True

    @staticmethod
    def supported_file_types():
        return ["*.sh", "*.bash"]

    def validate(self, path: str):
        try:
            check_call(["shellcheck", "-x", path])
        except CalledProcessError:
            raise ValidationError("failed to run shellcheck")
