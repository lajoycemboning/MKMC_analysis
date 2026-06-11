#!/bin/bash

working_dir=$1

dir=$working_dir"/feature/GSE216369_liver"

# Define the list of sample IDs
samples=("SRR22013770" "SRR22013769" "SRR22013763" "SRR22013765" "SRR22013762"
         "SRR22013789" "SRR22013780" "SRR22013782" "SRR22013784" "SRR22013775" "SRR22013787"
         "SRR22013785" "SRR22013786" "SRR22013779" "SRR22013774" "SRR22013793")

# Loop through each sample and process featureCounts output
for sample in "${samples[@]}"; do
    echo "Processing sample ${sample}"

    # Step 1: Locate the featureCounts file and create a clean counts file for the sample
    featureCounts_file=$(find "${dir}/${sample}" -name "*.featureCounts" | head -1)
    if [[ -z "$featureCounts_file" ]]; then
        echo "Error: No featureCounts file found for sample ${sample}."
        continue
    fi

    # Remove header, extract counts, and save to a clean counts file
    sed "1d" "$featureCounts_file" | cut -f7 > "${dir}/${sample}_clean.txt"

    # Check if the clean counts file was created successfully
    if [[ ! -f "${dir}/${sample}_clean.txt" ]]; then
        echo "Error: Failed to create clean counts file for sample ${sample}."
        continue
    fi

    # Step 2: Extract gene IDs from the featureCounts file for the sample
    cut -f1 "$featureCounts_file" | sed "1d" > "${dir}/${sample}_genes.txt"

    # Check if the genes file was created successfully
    if [[ ! -f "${dir}/${sample}_genes.txt" ]]; then
        echo "Error: Failed to create genes file for sample ${sample}."
        continue
    fi

    # Step 3: Combine gene IDs and counts into a matrix format
    paste "${dir}/${sample}_genes.txt" "${dir}/${sample}_clean.txt" > "${dir}/${sample}_matrix_new.txt"

    # Check if the final matrix file was created successfully
    if [[ ! -f "${dir}/${sample}_matrix_new.txt" ]]; then
        echo "Error: Failed to create matrix file for sample ${sample}."
    else
        echo "Matrix file created for sample ${sample}: ${dir}/${sample}_matrix_new.txt"
    fi
done
