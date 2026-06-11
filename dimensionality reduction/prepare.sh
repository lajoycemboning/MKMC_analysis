#!/bin/bash

# This script was not benchmarked in terms of time and memory requirements.

p_env=env

working_dir=working_path/GSE216369_liver
data=data_path/GSE216369_liver
prepare_threads=8
design=liver_sex_star.txt

python3 -m venv $p_env

source $p_env/bin/activate

pip install pandas
pip install scikit-learn
pip install umap-learn

conda deactivate

mkdir $working_dir

./1_generate_index.sh $working_dir $data $prepare_threads
./2_run_trim_galore.sh $working_dir $data $prepare_threads

echo "Run,sex" > $design
echo "SRR22013784,male" >> $design
echo "SRR22013785,male" >> $design
echo "SRR22013786,female" >> $design
echo "SRR22013780,female" >> $design
echo "SRR22013769,female" >> $design
echo "SRR22013763,female" >> $design
echo "SRR22013779,female" >> $design
echo "SRR22013793,female" >> $design
echo "SRR22013782,male" >> $design
echo "SRR22013774,male" >> $design
echo "SRR22013762,male" >> $design
echo "SRR22013770,female" >> $design
echo "SRR22013775,male" >> $design
echo "SRR22013765,male" >> $design
echo "SRR22013787,female" >> $design
echo "SRR22013789,male" >> $design
