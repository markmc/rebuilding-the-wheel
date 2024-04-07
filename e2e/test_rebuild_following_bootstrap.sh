#!/bin/bash

set -x
set -e
set -o pipefail

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TOPDIR="$( cd "${SCRIPTDIR}/.." && pwd )"

source "${SCRIPTDIR}/common.sh"
full_clean
setup

# Bootstrap a complex set of dependencies to get the build order. We
# use a simple dist here instead of langchain to avoid dependencies
# with rust parts so we can isolate the build environments when
# building one wheel at a time later.
python3 -m mirror_builder ${VERBOSE} bootstrap "stevedore"
BOOTSTRAP_OUTPUT=$WORKDIR/bootstrap-output.txt
find wheels-repo/downloads > $BOOTSTRAP_OUTPUT
BUILD_ORDER_FILE=${WORKDIR}/build-order-${PYTHON_VERSION}.json

# Remove the wheels-repo so it is rebuilt as we build those wheels again.
rm -rf wheels-repo

# Build the wheels one at a time in the same order.
BUILD_ONE_OUTPUT=$WORKDIR/build-one-output.txt
jq -r '.[] | .dist + " " + .version' "${BUILD_ORDER_FILE}" | while read name version; do
    WORKDIR=$(pwd)/work-dir-rebuild/${name}
    setup
    python3 -m mirror_builder --isolate-builds ${VERBOSE} build-one "$name" "$version"
done
find wheels-repo/downloads > $BUILD_ONE_OUTPUT

# We should get the same results
diff $BOOTSTRAP_OUTPUT $BUILD_ONE_OUTPUT
