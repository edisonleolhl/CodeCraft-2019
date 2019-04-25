#!/usr/bin/env bash

if [ ! -d "log" ]; then
  mkdir log
fi
export PYTHONIOENCODING=UTF-8
filename="log/chepai_reco`date +20%y_%m_%d___%H_%M_%S`.txt"
CUDA_VISIBLE_DEVICES=0 python -u chepai_ctcbaseline.py \
	2>&1 | tee $filename

