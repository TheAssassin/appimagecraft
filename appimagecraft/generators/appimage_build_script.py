import platform
import re
import shlex
from urllib.parse import urlparse

from appimagecraft._logging import get_logger
from appimagecraft._util import convert_kv_list_to_dict
from .bash_script import BashScriptGenerator


class AppImageBuildScriptGenerator:
    def __init__(self, ld_config: dict = None):
        if ld_config is None:
            ld_config = dict()

        self._config = ld_config

        self._logger = get_logger("scriptgen")

    def build_file(self, path: str):
        gen = BashScriptGenerator(path)

        arch = self._config.get("arch", platform.machine())

        valid_archs = ["x86_64", "i386"]

        # there's a few valid aliases for the known valid archs, which we can substitute automatically
        substitutes = {
            "amd64": "x86_64",
            "i586": "i386",
            "i686": "i386",
        }
        try:
            arch = substitutes[arch]
        except KeyError:
            pass

        if arch not in valid_archs:
            raise ValueError("Invalid arch: {}".format(arch))

        url = "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/" \
              "linuxdeploy-{}.AppImage".format(arch)

        gen.add_lines([
            "# fetch linuxdeploy from GitHub releases",
            "wget -c {}".format(shlex.quote(url)),
            "chmod +x linuxdeploy-{}.AppImage".format(arch),
        ])

        def build_official_plugin_url(name: str, filename: str = None):
            if filename is None:
                filename = "linuxdeploy-plugin-{name}-$ARCH.AppImage".format(name=name)

            return "https://github.com/linuxdeploy/linuxdeploy-plugin-{name}" \
                   "/releases/download/continuous/{filename}".format(name=name, filename=filename)

        known_plugin_urls = {
            "qt": build_official_plugin_url("qt"),
            "conda": "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-conda/master/"
                     "linuxdeploy-plugin-conda.sh",
        }

        ld_plugins = {}

        plugin_name_expr = r"^linuxdeploy-plugin-([^\s\.-]+)(?:-[^\.]+)?(?:\..+)?$"

        try:
            ld_plugins_config = self._config["linuxdeploy"]["plugins"]
        except KeyError:
            pass
        else:
            # required check for empty section
            if ld_plugins_config is not None:
                for plugin_entry in ld_plugins_config:
                    # check whether the entry is an absolute URL
                    parsed_url = urlparse(plugin_entry)
                    is_url = parsed_url.scheme and parsed_url.netloc and parsed_url.path

                    if is_url:
                        url = plugin_entry
                        # try to detect plugin name from URL
                        filename = url.split("/")[-1]
                        match = re.match(plugin_name_expr, filename)

                        if not match:
                            raise ValueError("Could not detect linuxdeploy plugin name from URL {}".format(url))

                        plugin_name = match.group(1)

                    else:
                        try:
                            url = known_plugin_urls[plugin_entry]
                        except KeyError:
                            raise ValueError("Unknown plugin: {}".format(plugin_entry))

                        plugin_name = plugin_entry

                    ld_plugins[plugin_name] = url

        for plugin_name, plugin_url in ld_plugins.items():
            # allow for inserting plugin architecture dynamically
            plugin_url = plugin_url.replace("$ARCH", arch)

            gen.add_lines([
                "# fetch {} plugin".format(plugin_name),
                "wget -c {}".format(shlex.quote(plugin_url)),
                "chmod +x linuxdeploy-plugin-{}*".format(shlex.quote(plugin_name))
            ])

        gen.add_line()

        # export environment vars listed in config
        try:
            env_config = self._config["linuxdeploy"]["environment"]
        except KeyError:
            pass
        else:
            try:
                dict(env_config)
            except ValueError:
                try:
                    iter(list)
                except ValueError:
                    raise ValueError("environment config is in invalid format")
                else:
                    # env_config = {i[0]: i[1] for i in (j.split("=") for j in env_config)}
                    env_config = convert_kv_list_to_dict(env_config)

            for env_var, value in dict(env_config).items():
                gen.add_line("export {}={}".format(shlex.quote(env_var), shlex.quote(value)))

            gen.add_line()

        # run linuxdeploy with the configured plugins
        ld_command = ["./linuxdeploy-{}.AppImage".format(arch), "--appdir", "AppDir", "--output", "appimage"]

        for plugin_name in ld_plugins.keys():
            ld_command.append("--plugin")
            ld_command.append(shlex.quote(plugin_name))

        # add extra arguments specified in config file
        extra_args = self._config.get("linuxdeploy", {}).get("extra_args")
        if extra_args is not None:
            if isinstance(extra_args, list):
                ld_command += extra_args
            elif isinstance(extra_args, str):
                ld_command.append(extra_args)
            else:
                raise ValueError("Invalid type for extra_args: {}".format(type(extra_args)))

        gen.add_line(" ".join(ld_command))

        gen.build_file()
