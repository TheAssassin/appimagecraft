#! /bin/bash

set -x
set -e

tmpdir=$(mktemp -d appimagecraft-XXXXXX)

cleanup() { rm -r "$tmpdir" ; }
trap cleanup EXIT

virtualenv "$tmpdir" -p $(which python3)
. "$tmpdir"/bin/activate

pip install -e .

appimagecraft build
