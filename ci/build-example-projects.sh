#! /bin/bash

set -e

log() {
    tput setaf 2
    tput bold
    echo "$@"
    tput sgr0
}

log "Set up test infrastructure"

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

log "Create virtualenvironment and install appimagecraft"

virtualenv -p $(which python3) venv
. venv/bin/activate

pip install "$REPO_ROOT"

log "Try out different commands on example CMake project"

pushd "$REPO_ROOT"/example-projects/cmake
log "-- Try genscripts command"
appimagecraft genscripts --build-dir "$WORKDIR"/cmake-genscripts
log "-- Clean up and recreate workdir for next command"
rm -r "$WORKDIR"/cmake
log "-- Try build command"
appimagecraft build --build-dir "$WORKDIR"/cmake
popd

log "Try out different commands on example autotools command"
log "-- Try genscripts command"
appimagecraft genscripts --build-dir "$WORKDIR"/autotools-genscripts
log "-- Clean up and recreate workdir for next command"
rm -r "$WORKDIR"/cmake
log "-- Try build command"
appimagecraft build --build-dir "$WORKDIR"/autotools
popd
