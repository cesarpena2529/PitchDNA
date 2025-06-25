import pandas as pd

# Load both files
df_original = pd.read_csv("pitcher_long_format_with_umap.csv")
df_ids = pd.read_csv("pitcher_name_to_id.csv")

# Get unique names from each
original_names = set(df_original["name"].dropna().unique())
id_names = set(df_ids["name"].dropna().unique())

# Find names in original not in id mapping
missing_names = original_names - id_names

print(f"Pitchers missing IDs: {len(missing_names)}")
for name in missing_names:
    print(name)