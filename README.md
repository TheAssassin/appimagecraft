# appimagecraft

Building AppImages made easy.


## About

appimagecraft completely automates the AppImage build process, building projects properly out of source and in temporary directories that allow for starting over in every build. This simulates a CI instance, and ensures that no step the developer did by hand can slip through and cause trouble on CI systems or other developers' workstations.

The tool was developed knowing that most code used to build AppImages on CI systems is copy-pasted from some examples, often just into a CI-specific format that cannot be run locally. This has a few major drawbacks:

- first of all, local testing consists of copy-pasting instructions from some other files, as most people don't write external scripts and call them from their CI scripts, and there's no way to run locally (*looking at you, Travis CI!*)
- many people state they don't want to know too much about the packaging, they just copy code until there's a result, often producing b-grade quality packages
- to change a minor aspect of packaging, you'd have to find the problem in a large script, instead of having a small compact representation of the process
- those scripts, once copy-pasted, never will be updated and therefore bugs cannot be fixed and new features or ideas won't ever reach people
- also, there's a lot of redundancy in people's AppImage build scripts, which shows that the process can be parametrized.

appimagecraft solves all these issues. appimagecraft just requires a small YAML file in the repository that define a few aspects of the project (e.g., what build system is used, how to fetch a version number, ...). With those few information, it can guess the required processes in order to build the project and turn it into an AppImage.

In contrary to many other tools that package applications, appimagecraft makes the entire process introspectable. It generates shell scripts (which it also can call after generation automatically). These scripts are simple to understand (no weird hackish boilerplate code). In case of issues, any developer can look into those scripts, there's no need to learn Python nor to read Python source code or add `print()`s in order to study the behavior of the build process.

appimagecraft should work for a majority of projects with properly written build scripts.


## Usage

appimagecraft requires a simple YAML-based file to lay in the repository root directory. Once the file has been written, you just have to run `appimagecraft` (or `appimagecraft build`) in the repository directory. appimagecraft creates a temporary directory and generates a bunch of shell scripts, all of which are called in the right order from a central script. Then, it runs the build scripts, ideally generates an AppImage and moves that back into your repository directory. Now, you should have an AppImage on hand!

If you want to just generate the scripts, you can run `appimagecraft genscripts -d build/`. This will just generate all the scripts in said directory and exit. You can then inspect the contents. If you want to run the build, just call the `build.sh` script inside that directory. Please beware that the directory will not be cleaned up automatically, and artifacts (such as AppImages) will remain within that directory as well.

For more information about the scripts, see [Contents of the build directory](#contents-of-the-build-directory).


## Use appimagecraft in a project

To use appimagecraft in a project, you have to create an `appimagecraft.yml` configuration in the root directory. Please see the [examples](https://github.com/TheAssassin/appimagecraft/tree/master/example-projects) to get an impression of which configuration flags are currently available. If you miss anything, please open a new issue, the list is far from complete.

The most minimal configuration for a regular CMake based project is:

```yml
version: 1

project:
  name: org.my.project
  version: 0.1.2
  # alternatively, you can specify a command that is run by appimagecraft to generate some version information, e.g.:
  # version_command: echo 1.2.3
  # version_command: git describe --tags
  # the command is run in your repository directory

build:
  cmake:

appimage:
  linuxdeploy:
```

Please note that this relies on a properly working CMake installation setup, which also installs a desktop file and at least one icon.

You can also specify a custom script to generate or copy files like so:

```yaml
scripts:
  post_build:
    - touch "$BUILD_DIR"/example.svg
    - |2
      cat > "$BUILD_DIR"/example.desktop <<EOF
      [Desktop Entry]
      Name=Example
      Type=Application
      Terminal=true
      Categories=Utility;
      Exec=example
      Icon=example
      EOF
```

You can use the environment variables `$PROJECT_ROOT` and `$BUILD_DIR` in those scripts. The path of the AppDir will be `"$BUILD_DIR"/AppDir`.

To customize the linuxdeploy process (e.g., making use of some plugins, setting custom environment variables or specifying additional parameters, you can customize the `appimage:` section:

```yml
appimage:
  linuxdeploy:
    plugins:
      #- qt
      #- conda
    environment:
      UPD_INFO: "zsync|http://foo.bar/baz.zsync"
    extra_args: -i "$BUILD_DIR"/example.svg -d "$BUILD_DIR"/example.desktop
```

Right now, only the official plugins can be specified by name in the `plugins:` section and be downloaded automatically. If you need additional plugins, the current workaround is to download them in a post-build script and then add `--plugin myplugin` to `extra_args`. This should be improved, please feel free to open an issue or comment an existing one.


## Contents of the build directory

*TODO*