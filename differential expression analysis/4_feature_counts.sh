#!/bin/bash

working_dir=$1
whole_input_dir=$2
threads=$3

feature_counts_output=$working_dir"/feature/GSE216369_liver"
uniquely_mapped_reads=$working_dir"/alignments/reads/GSE216369_liver"
gtf_dir=$whole_input_dir"/genomes/GFF/nfur"


# Define the list of sample IDs
samples=("SRR22013770" "SRR22013769" "SRR22013763" "SRR22013765" "SRR22013762"
         "SRR22013789" "SRR22013780" "SRR22013782" "SRR22013784" "SRR22013775" "SRR22013787"
         "SRR22013785" "SRR22013786" "SRR22013779" "SRR22013774" "SRR22013793")

# Create output directory if it doesn't exist
mkdir -p "$feature_counts_output"

# Loop through each sample and run featureCounts
for sample in "${samples[@]}"; do
    echo "Processing sample ${sample}"

    # Create a directory for each sample's featureCounts output
    mkdir -p "${feature_counts_output}/${sample}"

    # Count reads using featureCounts
    echo "Running featureCounts for sample ${sample}"
    echo "featureCounts -T 8 -p -a /home/lajoyce/mkmc/liver/trimmed_reads/GFF/nfur/ref_Nfu_20140520_top_level_filtered.gtf -g gene_name -o ${feature_counts_output}/${sample}/${sample}.featureCounts ${uniquely_mapped_reads}/${sample}/${sample}_UniquelyMapped.bam"
    
    featureCounts -T $threads -p \
        -a $gtf_dir/ref_Nfu_20140520_top_level_filtered.gtf \
        -g gene_name \
        -o "${feature_counts_output}/${sample}/${sample}.featureCounts" \
	"${uniquely_mapped_reads}/${sample}/${sample}_UniquelyMapped.bam"
done
