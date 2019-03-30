import os.path

from typing import List


def assert_not_none(data):
    if data is None:
        raise ValueError("data must not be None")


def get_appdir_path(build_dir: str):
    return os.path.abspath(os.path.join(build_dir, "AppDir"))


def convert_kv_list_to_dict(data: List[str]) -> dict:
    assert_not_none(data)

    rv = {}

    for i in data:
        k, v = i.split("=")

        if " " in k:
            raise ValueError("Invalid key format: {}".format(k))

        if k in rv:
            raise KeyError("keys must be unique ({} occurred more than once)".format(k))

        rv[k] = v

    return rv
