#!/bin/bash

working_dir=$1

design=liver_sex_star.txt

p_env=env
source $p_env/bin/activate

feature_counts_dir=$working_dir"/feature"
wrs_output_dir=$working_dir"/dim"

mkdir -p $wrs_output_dir/GSE216369_liver
python3 pca_umap.py $design $feature_counts_dir/GSE216369_liver > $wrs_output_dir/GSE216369_liver/dim_results.txt
