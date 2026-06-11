#!/bin/bash

working_dir=$1
whole_input_dir=$2
threads=$3

# Directory containing the raw fastq files
RAW_DIR=$whole_input_dir/reads

# Directory to save the trimmed reads
OUTPUT_DIR=$working_dir"/trimmed_reads/GSE216369_liver"

# Create output directory if it doesn't exist
mkdir -p $OUTPUT_DIR

# Loop through each sample and run trim_galore
for sample in SRR22013770 SRR22013769 SRR22013763 SRR22013765 SRR22013762 SRR22013789 SRR22013780 SRR22013782 SRR22013784 SRR22013775 SRR22013787 SRR22013785 SRR22013786 SRR22013779 SRR22013774 SRR22013793
do
    # Paired-end fastq files
    R1="${RAW_DIR}/${sample}_1.fastq.gz"
    R2="${RAW_DIR}/${sample}_2.fastq.gz"

    # Run trim_galore
    echo "Running trim_galore for sample ${sample}"
    trim_galore -j $threads --fastqc --fastqc_args "--outdir fastqc/${sample}" --gzip --output_dir ${OUTPUT_DIR}/${sample} --paired ${R1} ${R2}
done
