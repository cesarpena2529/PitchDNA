import pandas as pd
from pybaseball import playerid_lookup
from pybaseball.lahman import people
from rapidfuzz import process, fuzz

# Load your dataset
df = pd.read_csv("pitcher_long_format_with_umap.csv")
pitcher_names = df["name"].dropna().unique()
results = []

# Load the full player lookup table once
lookup_table = people()
lookup_table["full_name"] = lookup_table["name_first"].str.strip() + " " + lookup_table["name_last"].str.strip()
lookup_names = lookup_table["full_name"].tolist()

for name in pitcher_names:
    try:
        # Split name into last and first using comma
        found = False
        if "," in name:
            last, first = [part.strip() for part in name.split(",", 1)]
            lookup = playerid_lookup(last, first)
            if not lookup.empty:
                player_id = lookup.iloc[0]["key_mlbam"]
                results.append({"name": name, "player_id": player_id, "match_type": "exact", "matched_name": f"{first} {last}", "score": 100})
                found = True

        # If not found, try fuzzy matching
        if not found:
            # Convert "Last, First" to "First Last" for fuzzy matching
            if "," in name:
                last, first = [part.strip() for part in name.split(",", 1)]
                full_name = f"{first} {last}"
            else:
                full_name = name

            match, score, idx = process.extractOne(full_name, lookup_names, scorer=fuzz.token_sort_ratio)
            if score >= 90:
                matched_row = lookup_table.iloc[idx]
                player_id = matched_row["key_mlbam"]
                print(f"Fuzzy matched: {name} -> {match} (score: {score}, player_id: {player_id})")
                results.append({"name": name, "player_id": player_id, "match_type": "fuzzy", "matched_name": match, "score": score})
            else:
                print(f"No good match for: {name} (best: {match}, score: {score})")

    except Exception as e:
        print(f"Failed for {name}: {e}")

# Convert to DataFrame and save
id_df = pd.DataFrame(results)
id_df.to_csv("pitcher_name_to_id.csv", index=False)

print(f"✅ Found IDs for {len(id_df)} pitchers. Saved to pitcher_name_to_id.csv")


