import pandas as pd

# Load your files
umap_df = pd.read_csv("pitcher_long_format_with_umap.csv")
id_df = pd.read_csv("pitcher_name_to_id.csv")

# Merge on the 'name' column
merged = umap_df.drop(columns=['player_id'], errors='ignore').merge(id_df, on='name', how='left')

# Save to a new file (or overwrite if you wish)
merged.to_csv("pitcher_long_format_with_umap_with_ids.csv", index=False)

print("✅ player_id column added to pitcher_long_format_with_umap_with_ids.csv")