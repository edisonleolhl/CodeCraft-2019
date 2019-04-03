#!/bin/bash

SCRIPT=$(readlink -f "$0")
BASEDIR=$(dirname "$SCRIPT")
cd $BASEDIR

if [ ! -d CodeCraft-2019 ]
then
    echo "ERROR: $BASEDIR is not a valid directory of SDK_python for CodeCraft-2019."
    echo "  Please run this script in a regular directory of SDK_python."
    exit -1
fi

rm -f CodeCraft_code.tar.gz
tar -zcPf CodeCraft_code.tar.gz * --exclude=CodeCraft-2019/2-map-training-1 --exclude=CodeCraft-2019/2-map-training-2 --exclude=CodeCraft-2019/1-map-exam-1 --exclude=CodeCraft-2019/1-map-exam-2 --exclude=1-map-training-1 --exclude=1-map-training-2 --exclude=1-map-training-3 --exclude=1-map-training-4 --exclude=CodeCraft-2019/src/__pycache__ --exclude=CodeCraft-2019/src/simulator1.py --exclude=CodeCraft-2019/src/MapGenerator.py --exclude=CodeCraft-2019/src/test.py --exclude=CodeCraft-2019/DIY