import pandas as pd
from pybaseball import playerid_reverse_lookup
from rapidfuzz import process, fuzz

# Load your CSVs
umap_df = pd.read_csv('pitcher_long_format_with_umap.csv')
name_to_id_df = pd.read_csv('pitcher_name_to_id.csv')

umap_names = set(umap_df['name'].unique())
name_to_id_names = set(name_to_id_df['name'].unique())
missing_names = umap_names - name_to_id_names

# Get all MLBAM IDs in a reasonable range (modern players)
all_ids = list(range(400000, 800000))
player_table = playerid_reverse_lookup(all_ids, key_type='mlbam')
player_table["full_name"] = player_table["name_first"].str.strip() + " " + player_table["name_last"].str.strip()
lookup_names = player_table["full_name"].tolist()

matches = []
for name in missing_names:
    if "," in name:
        last, first = [part.strip() for part in name.split(",", 1)]
        full_name = f"{first} {last}"
    else:
        full_name = name

    match, score, idx = process.extractOne(full_name, lookup_names, scorer=fuzz.token_sort_ratio)
    matched_row = player_table.iloc[idx]
    player_id = matched_row["key_mlbam"]
    matches.append({
        'umap_name': name,
        'matched_name': match,
        'score': score,
        'player_id': player_id
    })
    print(f"Fuzzy matched: {name} -> {match} (score: {score}, player_id: {player_id})")

matches_df = pd.DataFrame(matches)
print(matches_df)
matches_df.to_csv('fuzzy_matches_for_missing_names.csv', index=False)