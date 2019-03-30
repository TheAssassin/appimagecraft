#! /bin/bash

set -e

if [[ "$CI" == "" ]] && [[ -d /dev/shm ]]; then
    export TMPDIR=/dev/shm
fi

WORKDIR=$(mktemp -d)

_cleanup() {
    [[ -d "$WORKDIR" ]] && rm -r "$WORKDIR"
}

trap _cleanup EXIT

REPO_ROOT=$(readlink -f $(dirname "$0")/..)

pushd "$WORKDIR"

virtualenv -p $(which python3) venv
. venv/bin/activate

pip install "$REPO_ROOT"

pushd "$REPO_ROOT"/example-projects/cmake
appimagecraft genscripts --build-dir "$WORKDIR"/cmake
popd

bash -x cmake/build.sh || bash

