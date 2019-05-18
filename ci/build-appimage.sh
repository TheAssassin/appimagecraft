#! /bin/bash

set -x
set -e

# use RAM disk if possible
if [ "$CI" == "" ] && [ -d /dev/shm ]; then
    TEMP_BASE=/dev/shm
else
    TEMP_BASE=/tmp
fi

BUILD_DIR=$(mktemp -d -p "$TEMP_BASE" appimagecraft-build-XXXXXX)

cleanup () {
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
    fi
}

trap cleanup EXIT

# store repo root as variable
REPO_ROOT=$(readlink -f $(dirname $(dirname "$0")))
OLD_CWD=$(readlink -f .)

pushd "$BUILD_DIR"

wget https://github.com/TheAssassin/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage
wget https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-conda/master/linuxdeploy-plugin-conda.sh

chmod +x linuxdeploy*.AppImage
chmod +x linuxdeploy*.sh


export PIP_REQUIREMENTS="."
export PIP_WORKDIR="$REPO_ROOT"
export OUTPUT=appimagecraft-x86_64.AppImage

cat > appimagecraft.desktop <<\EOF
[Desktop Entry]
Name=appimagecraft
Type=Application
Icon=appimagecraft
Exec=appimagecraft
NoDisplay=true
Terminal=true
Categories=Utility;
EOF

cat > AppRun.sh <<\EOF
#! /bin/bash

this_dir=$(dirname "$0")

# add own bin dir as fallback
# might come in handy if readelf binary is missing on the system (not sure if that's even possible, though)
export PATH="$PATH":"$this_dir"/usr/bin

"$this_dir"/usr/bin/python -m appimagecraft "$@"
EOF
chmod +x AppRun.sh

touch appimagecraft.svg
./linuxdeploy-x86_64.AppImage --appdir AppDir --plugin conda \
    -e $(which readelf) \
    -i appimagecraft.svg -d appimagecraft.desktop \
    --output appimage --custom-apprun AppRun.sh

mv appimagecraft*.AppImage "$OLD_CWD"
