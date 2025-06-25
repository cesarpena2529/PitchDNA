import pandas as pd
from pybaseball import playerid_lookup
from unidecode import unidecode
import difflib

# Load the dataset
df = pd.read_csv("pitcher_incorrect_pitcher_match.csv")

# Normalize names for matching
def normalize_name(name):
    return unidecode(name.strip().lower())

# Flip "Last, First" to "First Last"
def flip_name_format(name):
    try:
        last, first = name.split(", ")
        return f"{first} {last}"
    except:
        return name

# Function to verify player_id using pybaseball and return correct id
def verify_player_id(row):
    full_name = flip_name_format(row["name"])
    norm_name = normalize_name(full_name)
    try:
        lookup_result = playerid_lookup(full_name.split()[1], full_name.split()[0])
        for _, result_row in lookup_result.iterrows():
            result_name = normalize_name(f"{result_row['name_first']} {result_row['name_last']}")
            match_ratio = difflib.SequenceMatcher(None, norm_name, result_name).ratio()
            if match_ratio > 0.85:
                correct_id = int(result_row["key_mlbam"]) if not pd.isna(result_row["key_mlbam"]) else None
                is_correct = (
                    int(row["player_id"]) == correct_id if correct_id is not None and not pd.isna(row["player_id"]) else False
                )
                return pd.Series({
                    "correct_playerId": "correct" if is_correct else "incorrect",
                    "actual_player_id": correct_id
                })
        return pd.Series({"correct_playerId": "incorrect", "actual_player_id": None})
    except:
        return pd.Series({"correct_playerId": "incorrect", "actual_player_id": None})

# Apply the verification and get both columns
df[["correct_playerId", "actual_player_id"]] = df.apply(verify_player_id, axis=1)

# Save or inspect the result
df.to_csv("pitcher_verified_ids.csv", index=False)
print("✅ Done! Results saved to 'pitcher_verified_ids.csv'")
