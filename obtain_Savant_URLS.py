import pandas as pd
from pybaseball import statcast_pitcher, playerid_lookup
from sklearn.metrics.pairwise import euclidean_distances
import numpy as np
from unidecode import unidecode
import difflib

# Load your dataset
df = pd.read_csv("pitcher_long_format_with_validated_pitchers.csv")

CSV_FEATURES = ["avg_speed", "avg_spin", "avg_break_x", "avg_break_z"]
STATCAST_FEATURES = ["release_speed", "release_spin_rate", "pfx_x", "pfx_z"]
SAVE_EVERY = 100  # Save progress every 100 rows

def normalize_name(name):
    return unidecode(str(name).strip().lower())

def fuzzy_match_name(target, candidates):
    target_norm = normalize_name(target)
    best_match = None
    best_ratio = 0
    for cand in candidates:
        cand_norm = normalize_name(cand)
        ratio = difflib.SequenceMatcher(None, target_norm, cand_norm).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = cand
    return best_match, best_ratio

def get_player_id_from_name(name):
    # name is expected as "Last, First"
    try:
        last, first = name.split(", ")
    except ValueError:
        # fallback if not in expected format
        parts = name.split()
        last = parts[-1]
        first = " ".join(parts[:-1])
    lookup = playerid_lookup(last, first)
    if lookup.empty:
        return None
    # Fuzzy match to get the best candidate
    candidates = lookup["name_first"] + " " + lookup["name_last"]
    best, ratio = fuzzy_match_name(f"{first} {last}", candidates)
    if ratio > 0.85:
        idx = candidates[candidates == best].index[0]
        return lookup.loc[idx, "key_mlbam"]
    return None

def find_closest_pitch(row):
    name = row["name"]
    year = int(row["year"])
    pitch_type = str(row["pitch_type"]).upper()
    player_id = row.get("player_id", None)
    if pd.isna(player_id) or player_id in ["", "nan", None]:
        player_id = get_player_id_from_name(name)
    try:
        player_id = int(player_id)
    except Exception:
        player_id = get_player_id_from_name(name)
        if player_id is None or pd.isna(player_id):
            return "not found", "not found"

    try:
        pitches = statcast_pitcher(f"{year}-01-01", f"{year}-12-31", player_id)
    except Exception as e:
        print(f"Statcast download failed for {name} {year}: {e}")
        return "not found", "not found"

    pitches = pitches.dropna(subset=["pitch_type"])
    pitches["pitch_type"] = pitches["pitch_type"].astype(str)
    pitches = pitches[pitches["pitch_type"].str.upper() == pitch_type]

    if pitches.empty:
        print(f"No pitches found for {name} ({player_id}) {year} {pitch_type}")
        return "not found", "not found"

    # Convert pfx_x and pfx_z from feet to inches
    if "pfx_x" in pitches.columns:
        pitches["pfx_x"] = pitches["pfx_x"] * 12
    if "pfx_z" in pitches.columns:
        pitches["pfx_z"] = pitches["pfx_z"] * 12

    available_features = []
    row_features = []
    for csv_f, statcast_f in zip(CSV_FEATURES, STATCAST_FEATURES):
        if pd.notna(row[csv_f]) and statcast_f in pitches.columns and pitches[statcast_f].notna().any():
            available_features.append(statcast_f)
            row_features.append(row[csv_f])

    if not available_features:
        print(f"No usable features for {name} ({player_id}) {year} {pitch_type}")
        return "not found", "not found"

    pitches = pitches.dropna(subset=available_features)
    if pitches.empty:
        print(f"No complete pitches for {name} ({player_id}) {year} {pitch_type}")
        return "not found", "not found"

    avg_features = np.array([row_features])
    pitch_features = pitches[available_features].values

    try:
        dists = euclidean_distances(avg_features, pitch_features)
        min_idx = np.argmin(dists)
        closest = pitches.iloc[min_idx]
        return closest.get("game_pk", "not found"), closest.get("pitch_number", "not found")
    except Exception as e:
        print(f"Distance calculation failed for {name} ({player_id}) {year} {pitch_type}: {e}")
        return "not found", "not found"

# Prepare columns
df["game_pk"] = "not found"
df["pitch_number"] = "not found"

for idx, row in df.iterrows():
    print(f"Processing row {idx+1}/{len(df)}: {row['name']} ({row['year']}, {row['pitch_type']})")
    try:
        game_pk, pitch_number = find_closest_pitch(row)
    except Exception as e:
        print(f"Error on row {idx}: {e}")
        game_pk, pitch_number = "not found", "not found"
    df.at[idx, "game_pk"] = game_pk
    df.at[idx, "pitch_number"] = pitch_number

    # Incremental save
    if (idx + 1) % SAVE_EVERY == 0 or (idx + 1) == len(df):
        df.to_csv("pitcher_verified_ids_with_gamepk_pitchnum.csv", index=False)
        print(f"Progress saved at row {idx + 1}/{len(df)}")

print("✅ Finished! All progress saved to pitcher_verified_ids_with_gamepk_pitchnum.csv")