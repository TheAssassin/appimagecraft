#! /bin/bash

this_dir="$(dirname "$0")"

# we only bundle shellcheck for platforms for which shellcheck officially provides static binaries
# our launch script therefore needs to check whether such a binary can be found in the AppDir
# appimagecraft uses this binary if it exists, otherwise falls back to checking $PATH
SHELLCHECK="$this_dir/usr/bin/shellcheck"
[[ -f "$SHELLCHECK" ]] && export SHELLCHECK

exec "$this_dir"/usr/bin/python -m appimagecraft "$@"
