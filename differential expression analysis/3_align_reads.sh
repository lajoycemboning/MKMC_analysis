#!/bin/bash

working_dir=$1
threads=$2

ulimit -n 4096

# Define the list of sample IDs
samples=("SRR22013770" "SRR22013769" "SRR22013763" "SRR22013765" "SRR22013762"
         "SRR22013789" "SRR22013780" "SRR22013782" "SRR22013784" "SRR22013775" "SRR22013787"
         "SRR22013785" "SRR22013786" "SRR22013779" "SRR22013774" "SRR22013793")

# Define paths for genome directory and output base directories
genome_dir=$working_dir"/index/GCF_001465895.1/genome_index"
fastq_dir_base=$working_dir"/trimmed_reads/GSE216369_liver"  # Base directory for fastq files
output_dir_base=$working_dir"/alignments/reads/GSE216369_liver"  # Base directory for output

# Create output directory if it doesn't exist
mkdir -p "$output_dir_base"

# Loop through each sample and run STAR and samtools
for sample in "${samples[@]}"; do
    echo "Processing sample ${sample}"

    # Make sure output directory for the sample exists
    mkdir -p "${output_dir_base}/${sample}"

    # STAR: Align reads
    echo "Running STAR alignment for sample ${sample}"
    STAR --runThreadN $threads \
         --genomeDir "$genome_dir" \
         --readFilesIn "${fastq_dir_base}/${sample}/${sample}_1_val_1.fq.gz" "${fastq_dir_base}/${sample}/${sample}_2_val_2.fq.gz" \
         --readFilesCommand zcat \
         --outSAMtype BAM SortedByCoordinate \
         --outFileNamePrefix "${output_dir_base}/${sample}/${sample}_"

    # Check if STAR alignment succeeded
    if [ $? -ne 0 ]; then
        echo "Error: STAR alignment failed for sample ${sample}. Check input paths or STAR installation."
        continue
    fi

    # FILTER BAM: Keep uniquely mapped reads
    echo "Filtering uniquely mapped reads for sample ${sample}"
    samtools view -q 255 -b "${output_dir_base}/${sample}/${sample}_Aligned.sortedByCoord.out.bam" > "${output_dir_base}/${sample}/${sample}_UniquelyMapped.bam"

    # Check if samtools filtering succeeded
    if [ $? -ne 0 ]; then
        echo "Error: samtools filtering failed for sample ${sample}. Check samtools installation or input BAM file."
        continue
    fi

    echo "Sample ${sample} processing completed."
done
