import os.path
import yaml


class AppImageCraftYMLParser:
    def __init__(self, config_path):
        if not os.path.exists(config_path):
            raise IOError("Config file {} does not exist".format(config_path))

        self._config_path = config_path
        self._data = None

        self._parse()
        self._validate()

    def _parse(self):
        with open(self._config_path, "r") as f:
            self._data = yaml.safe_load(f.read())

    def data(self):
        return dict(self._data)

    # validates parsed data
    # validation only takes place to some extent
    # the validator only guarantees correctness on a root level, builder-specific stuff needs to be validated there
    def _validate(self):
        c: dict = self._data

        def _assert(condition, message):
            if not condition:
                if not message:
                    message = "Unknown error while parsing appimagecraft config"

                raise ValueError(message)

        def assert_reverse_dns_format(data):
            message = "project name must be in "
            _assert(not data.endswith("."), message)
            _assert(not data.startswith("."), message)
            _assert(data.count(".") > 0, message)
            # TODO: check there's at least one char between periods

        valid_root_keys = {"version", "project", "build", "environment", "appimage", "scripts"}
        required_root_keys = {"version", "project", "build"}

        all_root_keys = set(c.keys())

        invalid_root_keys = list(all_root_keys - valid_root_keys)
        if invalid_root_keys:
            raise ValueError("invalid key in config: {}".format(invalid_root_keys[0]))

        missing_root_keys = list(required_root_keys - all_root_keys)
        if missing_root_keys:
            raise ValueError("missing key in config: {}".format(missing_root_keys[0]))

        # check file version
        version = c["version"]
        _assert(version == 1, "unsupported config file version: {}".format(version))

        if not isinstance(c["project"], dict):
            raise ValueError("project: data must be in key: value format")

        if "name" not in c["project"]:
            raise ValueError("project name missing")

        # project name should be in reverse DNS style, similar to AppStream
        assert_reverse_dns_format(c["project"]["name"])
