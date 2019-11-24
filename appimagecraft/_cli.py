import argparse
import logging
import os.path
import sys
import tempfile
import textwrap

from .parsers import AppImageCraftYMLParser
from . import _logging
from .commands import *  # noqa


def parse_args():
    parser = argparse.ArgumentParser(description="appimagecraft -- woo!")

    parser.add_argument("-f", "--config-file",
                        nargs="?", dest="config_file",
                        help="Path to appimagecraft config", default="appimagecraft.yml")

    parser.add_argument("-b", "--builder",
                        nargs="?", dest="builder_name",
                        help="Name of builder to use (default: first listed)")

    parser.add_argument("-d", "--build-dir",
                        nargs="?", dest="build_dir",
                        help="Path to build directory (default: auto-generated)")

    parser.add_argument("--list-commands",
                        dest="list_commands",
                        action="store_const", const=True, default=False,
                        help="List available commands")

    parser.add_argument("--debug",
                        dest="loglevel",
                        action="store_const", const=logging.DEBUG, default=logging.INFO,
                        help="Display debug messages")

    parser.add_argument("--log-source-location",
                        dest="log_message_locations",
                        action="store_const", const=True, default=False,
                        help="Print message locations (might be picked up by IDEs to allow for jumping to the source)")

    parser.add_argument("--log-timestamps",
                        dest="log_timestamps",
                        action="store_const", const=True, default=False,
                        help="Log timestamps (useful for debugging build times etc.)")

    parser.add_argument("--force-colors",
                        dest="force_colors",
                        action="store_const", const=True, default=False,
                        help="Force colored output")

    parser.add_argument("command",
                        nargs="?", help="Command to run (default: build)", default="build")

    args = parser.parse_args()

    if args.list_commands:
        commands = """
            Available commands:
                build:       build current project
                genscripts:  generate build scripts in current directory
                setup:       setup appimagecraft for this project (interactively)
        """

        print(textwrap.dedent(commands).strip("\n"))

        sys.exit(0)

    return args


def run():
    args = parse_args()

    # setup
    _logging.setup(
        args.loglevel,
        with_timestamps=args.log_timestamps,
        force_colors=args.force_colors,
        log_locations=args.log_message_locations,
    )

    # get logger for CLI
    logger = _logging.get_logger("cli")

    yml_parser = AppImageCraftYMLParser(args.config_file)
    config = yml_parser.data()

    logger.info("Building project {}".format(config["project"]["name"]))

    command_name = getattr(args, "command", None)

    if command_name is None:
        command_name = "build"

    commands_classes_map = {
        "build": BuildCommand,
        "genscripts": GenerateScriptsCommand,
        # "setup": SetupCommand,
    }

    # project root dir = location of config file
    project_root_dir = os.path.abspath(os.path.dirname(args.config_file))

    # set up args
    build_dir = getattr(args, "build_dir", None)
    builder_name = getattr(args, "builder_name", None)

    # set default values
    if builder_name is None:
        try:
            # use first builder as fallback
            builder_name = list(config["build"].keys())[0]
        except KeyError:
            logger.critical("no builder configured in config file")
            sys.exit(1)

    if build_dir is None:
        if command_name != "build":
            # commands like genscripts aren't very helpful if the user doesn't take care of managing the build
            # directory; they want to call the scripts, after all
            logger.critical("cannot use auto-generated build dir with commands other than build, "
                            "please specify build dir with -d/--build-dir")
            sys.exit(1)
        else:
            build_dir = tempfile.mkdtemp(prefix=".appimagecraft-build-{}-".format(builder_name),
                                         dir=os.path.dirname(args.config_file))

    # make sure build_dir is absolute
    build_dir = os.path.abspath(build_dir)

    # make sure build dir exists
    if not os.path.isdir(build_dir):
        logger.info("Creating directory {}".format(build_dir))
        os.mkdir(build_dir)

    logger.info("Building in directory {}".format(build_dir))
    logger.info("Building with builder {}".format(builder_name))

    # ensure correct permissions on build dir
    os.chmod(build_dir, 0o755)

    # get command instance
    command = None

    try:
        command_class = commands_classes_map[command_name]
    except KeyError:
        pass
    else:
        command = command_class(config, project_root_dir, build_dir, builder_name)

    if command is None:
        logger.critical("No such command: {}".format(command_name))
        sys.exit(1)

    try:
        command.run()
    except NotImplementedError as e:
        logger.exception(e)
    except KeyboardInterrupt:
        logger.critical("process interrupted by user")
        sys.exit(1)
