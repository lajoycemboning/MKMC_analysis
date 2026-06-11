#!/bin/bash

# This script was benchmarked in terms of time and memory requirements.

working_dir=working_path/GSE216369_liver
data=data_path/GSE216369_liver
threads=32

./3_align_reads.sh $working_dir $threads
./4_feature_counts.sh $working_dir $data $threads
./5_count_matrix.sh $working_dir
./6_run_python.sh $working_dir
