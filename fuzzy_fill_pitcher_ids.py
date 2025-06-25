import pandas as pd
from rapidfuzz import process, fuzz

# Load both files
df_original = pd.read_csv("pitcher_long_format_with_umap.csv")
df_ids = pd.read_csv("pitcher_name_to_id.csv")

original_names = set(df_original["name"].dropna().unique())
id_names = set(df_ids["name"].dropna().unique())

missing_names = original_names - id_names

# Prepare a list to store new matches
new_matches = []

# Set a threshold for fuzzy matching confidence
FUZZY_THRESHOLD = 90

for name in missing_names:
    # Find the best fuzzy match in the ID-mapped names
    match, score, _ = process.extractOne(name, id_names, scorer=fuzz.token_sort_ratio)
    if score >= FUZZY_THRESHOLD:
        # Get the player_id for the matched name
        player_id = df_ids[df_ids["name"] == match]["player_id"].values[0]
        print(f"Auto-adding: {name} -> {match} (score: {score}, player_id: {player_id})")
        new_matches.append({"name": name, "player_id": player_id})
    else:
        print(f"NO GOOD MATCH: {name} (best: {match}, score: {score})")

# Append new matches to the ID DataFrame and save
if new_matches:
    df_ids = pd.concat([df_ids, pd.DataFrame(new_matches)], ignore_index=True)
    df_ids.to_csv("pitcher_name_to_id_fuzzy.csv", index=False)
    print(f"\n✅ Added {len(new_matches)} fuzzy matches. Saved to pitcher_name_to_id_fuzzy.csv")
else:
    print("\nNo fuzzy matches added.")