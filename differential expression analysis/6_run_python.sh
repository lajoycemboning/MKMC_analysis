#!/bin/bash

working_dir=$1

p_env=env
source $p_env/bin/activate

feature_counts_dir=$working_dir"/feature"
wrs_output_dir=$working_dir"/wrs_cor"

mkdir -p $wrs_output_dir/GSE216369_liver

python3 mann.py $feature_counts_dir/GSE216369_liver > $wrs_output_dir/GSE216369_liver/significant_results.txt
