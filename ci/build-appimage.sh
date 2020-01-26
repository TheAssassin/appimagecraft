#! /bin/bash

set -x
set -e

tmpdir=$(mktemp -d appimagecraft-XXXXXX)

cleanup() { rm -r "$tmpdir" ; }
trap cleanup EXIT

virtualenv "$tmpdir" -p $(which python3)
. "$tmpdir"/bin/activate

pip install -e .


EXTRA_ARGS=()

case "$ARCH" in
    i386|i686)
        EXTRA_ARGS=("-f" "appimagecraft-i386.yml")
        ;;
esac

appimagecraft build "${EXTRA_ARGS[@]}"
