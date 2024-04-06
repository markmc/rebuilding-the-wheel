#!/bin/bash

set -x
set -e
set -o pipefail

toplevel=${1:-langchain}

PYTHON_TO_TEST="
  python3.9
  python3.12
"

for PYTHON in $PYTHON_TO_TEST; do
    jq -r '.[] | .dist + " " + .version' work-dir-bootstrap/build-order-$($PYTHON --version | cut -f2 -d' ').json | while read name version; do
        PYTHON=$PYTHON ./build-wheel.sh $name $version
    done
done
