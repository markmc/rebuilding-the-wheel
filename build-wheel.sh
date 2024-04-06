#!/bin/bash
# -*- indent-tabs-mode: nil; tab-width: 2; sh-indentation: 2; -*-

set -xe
set -o pipefail
export PS4='+ ${BASH_SOURCE#$HOME/}:$LINENO \011'

name="$1"; shift
version="$1"; shift

VERBOSE=${VERBOSE:-}
if [ -n "${VERBOSE}" ]; then
  VERBOSE="-v"
fi
VERBOSE="-v"

DEFAULT_WORKDIR=$(pwd)/work-dir-build-one
export WORKDIR=${WORKDIR:-${DEFAULT_WORKDIR}}
mkdir -p $WORKDIR

PYTHON=${PYTHON:-python3.9}
PYTHON_VERSION=$($PYTHON --version | cut -f2 -d' ')

# Redirect stdout/stderr to logfile
logfile="$WORKDIR/build-wheel-${name}-${version}-py${PYTHON_VERSION}.log"
exec > >(tee "$logfile") 2>&1

VENV="${WORKDIR}/venv-build-${PYTHON}"
# Create a fresh virtualenv every time since the process installs
# packages into it.
rm -rf "${VENV}"
"${PYTHON}" -m venv "${VENV}"
source "${VENV}/bin/activate"
pip install --upgrade pip
pip install -e .

python3 -m mirror_builder ${VERBOSE} build-one "$name" "$version"
