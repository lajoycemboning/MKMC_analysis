#!/bin/bash

# This script was not benchmarked in terms of time and memory requirements.

p_env=env

working_dir=working_path/GSE216369_liver
data=data_path/GSE216369_liver
prepare_threads=8

python3 -m venv $p_env

source $p_env/bin/activate

pip install numpy
pip install pandas
pip install scipy
pip install statsmodels

conda deactivate

mkdir $working_dir

./1_generate_index.sh $working_dir $data $prepare_threads
./2_run_trim_galore.sh $working_dir $data $prepare_threads
