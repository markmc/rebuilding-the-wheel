#!/bin/bash

export PS4='+ ${BASH_SOURCE#$HOME/}:$LINENO \011'

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOPDIR="$( cd "${SCRIPTDIR}/.." && pwd )"

VERBOSE=${VERBOSE:-}
if [ -n "${VERBOSE}" ]; then
  VERBOSE="-v"
fi

DEFAULT_WORKDIR=$(pwd)/work-dir
export WORKDIR=${WORKDIR:-${DEFAULT_WORKDIR}}

export PYTHON=${PYTHON:-python3.12}
PYTHON_VERSION=$($PYTHON --version | cut -f2 -d' ')

setup() {
    rm -rf $WORKDIR
    mkdir -p $WORKDIR

    # Create a fresh virtualenv every time since the process installs
    # packages into it.
    VENV="${WORKDIR}/venv-${PYTHON}"
    rm -rf "${VENV}"
    "${PYTHON}" -m venv "${VENV}"
    source "${VENV}/bin/activate"
    pip install --upgrade pip
    (cd "$TOPDIR" && pip install -e .)
}

full_clean() {
    rm -rf $TOPDIR/wheels-repo $TOPDIR/sdists-repo
    rm -rf $WORKDIR
}
