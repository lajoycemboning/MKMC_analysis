#!/bin/bash

working_dir=$1
whole_input_dir=$2
prepare_threads=$3

# Paths to directories and files
genome_index_dir=$working_dir"/index/GCF_001465895.1"
genome_files_dir=$whole_input_dir"/genomes/ncbi_dataset/data/GCF_001465895.1"
gtf_dir=$whole_input_dir"/genomes/GFF/nfur"

# Run STAR genome generation without sjdbOverhang
STAR --runThreadN $prepare_threads \
	--runMode genomeGenerate \
	--genomeDir $genome_index_dir/genome_index \
	--genomeFastaFiles $genome_files_dir/GCF_001465895.1_Nfu_20140520_genomic.fna \
	--sjdbGTFfile $gtf_dir/ref_Nfu_20140520_top_level_filtered.gtf \
	--sjdbOverhang 149
