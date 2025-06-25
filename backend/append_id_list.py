import pandas as pd

# Load the main mapping file
main_df = pd.read_csv("pitcher_name_to_id.csv")

# Load the fuzzy matches file
fuzzy_df = pd.read_csv("fuzzy_matches_for_missing_names.csv")

# Select only the name and player_id columns
fuzzy_subset = fuzzy_df[["name", "player_id"]]

# Concatenate and drop duplicates
combined = pd.concat([main_df, fuzzy_subset], ignore_index=True)
combined = combined.drop_duplicates(subset=["name"], keep="first")

# Save back to the main file
combined.to_csv("pitcher_name_to_id.csv", index=False)

print("✅ Fuzzy matches added to pitcher_name_to_id.csv")