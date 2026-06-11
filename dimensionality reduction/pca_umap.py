import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.decomposition import PCA
import umap
import sys


n_args = len(sys.argv)
if n_args != 3:
    print ("Pass input file name and directory", file=sys.stderr)
    exit(1)
directory=sys.argv[2]
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

df = df.T

metadata_liver = pd.read_csv(sys.argv[1])
metadata_liver.set_index("Run", inplace=True)

main_matrix_ordered = df.loc[metadata_liver.index.tolist(), ]
main_matrix_ordered = main_matrix_ordered.div(main_matrix_ordered.sum(axis=1), axis=0)

# Perform UMAP
umap_model = umap.UMAP(n_components=2, random_state=42)  # Set random_state for reproducibility
umap_components = umap_model.fit_transform(main_matrix_ordered)
print("UMAP")
print(umap_components)

# Perform PCA
pca = PCA(n_components=2, random_state=42) # Adjust n_components if needed
principal_components = pca.fit_transform(main_matrix_ordered)
print("PCA")
print(principal_components)
print(pca.explained_variance_ratio_[0])
print(pca.explained_variance_ratio_[1])
