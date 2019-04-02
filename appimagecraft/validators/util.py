import fnmatch
import os.path

from typing import List, Type

from . import ValidatorBase, __all__ as _all_validators


def _get_validators_map() -> dict:
    validators: List[ValidatorBase] = _all_validators
    validators.remove(ValidatorBase)

    rv = {v: v.supported_file_types() for v in validators}
    return rv


def get_validator(path: str) -> Type[ValidatorBase]:
    """
    Create suitable validator for provided path.

    :param path: path to file
    :return: the suitable validator
    :raises KeyError: in case no suitable validator could be found
    :raises ValueError: if there are multiple suitable validators and we can't decide which one to use (should not happen!)
    """

    validators_map = _get_validators_map()

    suitable_validators = set()

    for validator, patterns in validators_map.items():
        for pattern in patterns:
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                suitable_validators.add(validator)

    if len(suitable_validators) > 1:
        raise ValueError("multiple suitable validators found for path {}".format(path))
    elif len(suitable_validators) < 1:
        raise KeyError("could not find suitable validator for path {}")

    return suitable_validators.pop()


def validate_file(path: str):
    """
    Try to validate file.

    :param path: path to file to validate
    :raises KeyError: if no validator is available
    :raises ValueError: if there are multiple suitable validators and we can't decide which one to use (should not happen!)
    :raises ValidationError: if validation fails
    """

    validator_class = get_validator(path)
    validator = validator_class()
    validator.validate(path)
