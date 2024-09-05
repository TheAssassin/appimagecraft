#! /bin/bash

set -x
set -e

tmpdir=$(mktemp -d appimagecraft-XXXXXX)

cleanup() { rm -r "$tmpdir" ; }
trap cleanup EXIT

"${PYTHON:-python3}" -m venv "$tmpdir"
. "$tmpdir"/bin/activate

pip install .


EXTRA_ARGS=()

case "$ARCH" in
    i386|i686)
        EXTRA_ARGS=("-f" "appimagecraft-i386.yml")
        ;;
    aarch64)
	EXTRA_ARGS=("-f" "appimagecraft-aarch64.yml")
	;;
esac

appimagecraft build "${EXTRA_ARGS[@]}"
