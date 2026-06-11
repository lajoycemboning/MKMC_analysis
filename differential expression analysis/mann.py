#!/bin/env python3
import pandas as pd
import sys
from scipy.stats import mannwhitneyu
from scipy.stats import ranksums
from statsmodels.stats.multitest import multipletests
import sys
import os

n_args = len(sys.argv)
if n_args != 2:
    print ("Pass input file name", file=sys.stderr)
    exit(1)
directory=sys.argv[1]
# Get a list of all files matching the pattern 'SRR*_matrix_new.txt'
files = [f for f in os.listdir(directory) if f.endswith('_matrix_new.txt')]

# Initialize an empty list to store dataframes
dfs = []

# Loop through each file, read it, and append to the list of dataframes
for file in files:
    file_path = os.path.join(directory, file)
    df = pd.read_csv(file_path, sep='\t', header=None, skiprows=1, names=['Geneid', file.split('_')[0]])  # Skip the first row
    dfs.append(df)

df = dfs[0]  # Start with the first dataframe

for idf in dfs[1:]:
    df = df.merge(idf, on='Geneid', how='outer')

df.set_index("Geneid", inplace=True)

df = df.T

# Define the male and female groups based on your mapping
male_samples = ["SRR22013762", "SRR22013765", "SRR22013774", "SRR22013775", 
                "SRR22013782", "SRR22013784", "SRR22013785", "SRR22013789"]
female_samples = ["SRR22013763", "SRR22013769", "SRR22013770", "SRR22013779", 
                  "SRR22013780", "SRR22013786", "SRR22013787", "SRR22013793"]
data_norm = df.div(df.sum(axis=1), axis=0)

# Filter data for male and female samples
male_data = data_norm.loc[male_samples]
female_data = data_norm.loc[female_samples]

# Ensure alignment by checking if both datasets have the same genes (columns)
assert list(male_data.columns) == list(female_data.columns), "Mismatch in gene names between male and female datasets."

# Perform Mann-Whitney U Test for each gene
results = []
genes = []
for gene in df.columns:  # Iterate over genes directly, as they are columns
#    stat, p_value = mannwhitneyu(male_data[gene], female_data[gene], alternative='two-sided')
    stat, p_value = ranksums(male_data[gene], female_data[gene])
    results.append(p_value)
    genes.append(gene)

_, adj_p_values, _, _ = multipletests(results, alpha=0.05, method='fdr_bh')

# Convert results to DataFrame
results_df = pd.DataFrame({
    'Gene': genes,
    'p_value': results,
    'Adjusted P-value': adj_p_values
})

# Apply a significance threshold
significant_genes = results_df[results_df['Adjusted P-value'] < 0.05]

# Print significant genes
pd.set_option('display.max_rows', None)
print("Significant Genes:")
print(significant_genes)
