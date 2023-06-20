import platform
import re
import shlex
from urllib.parse import urlparse

from appimagecraft._logging import get_logger
from appimagecraft._util import convert_kv_list_to_dict
from .bash_script import ProjectAwareBashScriptBuilder


class AppImageBuildScriptGenerator:
    def __init__(self, ld_config: dict = None):
        if ld_config is None:
            ld_config = dict()

        self._config = ld_config

        self._logger = get_logger("scriptgen")

    def build_file(self, path: str, project_root_dir: str, build_dir: str):
        gen = ProjectAwareBashScriptBuilder(path, project_root_dir, build_dir)

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

        url = (
            "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/"
            "linuxdeploy-{}.AppImage".format(arch)
        )

        # change to custom directory
        gen.add_lines(
            [
                "# switch to separate build dir",
                "mkdir -p appimage-build",
                "cd appimage-build",
                "",
            ]
        )

        # export architecture, might be used by some people
        gen.add_lines(
            [
                "export ARCH={}".format(shlex.quote(arch)),
                "",
            ]
        )

        gen.add_lines(
            [
                "# we store all downloaded files in a separate directory so we can easily skip them when moving the artifacts around",
                "mkdir -p downloads",
                "pushd downloads",
                "",
            ]
        )

        gen.add_lines(
            [
                "# fetch linuxdeploy from GitHub releases",
                "wget -c {}".format(shlex.quote(url)),
                "chmod +x linuxdeploy-{}.AppImage".format(arch),
            ]
        )

        def build_official_plugin_url(name: str, filename: str = None):
            if filename is None:
                filename = "linuxdeploy-plugin-{name}-$ARCH.AppImage".format(name=name)

            return (
                "https://github.com/linuxdeploy/linuxdeploy-plugin-{name}"
                "/releases/download/continuous/{filename}".format(name=name, filename=filename)
            )

        def build_official_shell_script_plugin_url(name: str):
            return (
                f"https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-{name}/master/"
                f"linuxdeploy-plugin-{name}.sh"
            )

        def build_official_misc_plugin_url(name: str):
            return (
                f"https://raw.githubusercontent.com/linuxdeploy/misc-plugins/master/{name}/"
                f"linuxdeploy-plugin-{name}.sh"
            )

        known_plugin_urls = {
            "qt": build_official_plugin_url("qt"),
        }

        for plugin_name in ["conda", "gtk", "perl", "gstreamer", "ncurses"]:
            known_plugin_urls[plugin_name] = build_official_shell_script_plugin_url(plugin_name)

        for misc_plugin_name in ["gdb", "gettext"]:
            known_plugin_urls[misc_plugin_name] = build_official_misc_plugin_url(plugin_name)

        ld_plugins = {}

        plugin_name_expr = r"^linuxdeploy-plugin-([^\s\.-]+)(?:-[^\.]+)?(?:\..+)?$"

        try:
            ld_plugins_config = (self._config.get("linuxdeploy", None) or {}).get("plugins", {})
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

            gen.add_lines(
                [
                    "# fetch {} plugin".format(plugin_name),
                    "wget -c {}".format(shlex.quote(plugin_url)),
                    "chmod +x linuxdeploy-plugin-{}*".format(shlex.quote(plugin_name)),
                ]
            )

        gen.add_line()

        gen.add_lines(["# we're done downloading, let's move back to the root directory", "popd", ""])

        # export environment vars listed in config
        def try_export_env_vars(key_name, raw=False):
            try:
                env_config = (self._config.get("linuxdeploy", None) or {}).get(key_name, {})
            except KeyError:
                pass
            else:
                try:
                    dict(env_config)
                except ValueError:
                    try:
                        iter(env_config)
                    except ValueError:
                        raise ValueError("environment config is in invalid format")
                    else:
                        env_config = convert_kv_list_to_dict(env_config)

                gen.add_line("# environment variables from {}".format(key_name))
                gen.export_env_vars(env_config, raw=raw)

                # add some space between this and the next block
                gen.add_line()

        try_export_env_vars("environment")
        try_export_env_vars("raw_environment", raw=True)

        # run linuxdeploy with the configured plugins
        ld_command = [
            "./downloads/linuxdeploy-{}.AppImage".format(arch),
            "--appdir",
            "../AppDir",
            "--output",
            "appimage",
        ]

        for plugin_name in ld_plugins.keys():
            ld_command.append("--plugin")
            ld_command.append(shlex.quote(plugin_name))

        # add extra arguments specified in config file
        extra_args = (self._config.get("linuxdeploy", None) or {}).get("extra_args", None)
        if extra_args is not None:
            if isinstance(extra_args, list):
                ld_command += extra_args
            elif isinstance(extra_args, str):
                ld_command.append(extra_args)
            else:
                raise ValueError("Invalid type for extra_args: {}".format(type(extra_args)))

        gen.add_line(" ".join(ld_command))

        gen.add_lines(
            [
                "",
                "# move built AppImages to artifacts dir, excluding the downloaded linuxdeploy stuff",
                "find . -type f -path ./downloads -prune -o -iname '*.AppImage*' -exec mv '{}' ../artifacts ';'",
            ]
        )

        gen.build_file()
