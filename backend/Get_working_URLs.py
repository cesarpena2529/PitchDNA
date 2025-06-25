import pandas as pd
import requests
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances
from unidecode import unidecode
import difflib

CSV_FEATURES = ["avg_speed", "avg_spin", "avg_break_x", "avg_break_z"]
JSON_FEATURES = ["startSpeed", "spinRate", "breakX", "breakZ"]

def normalize_name(name):
    return unidecode(str(name).strip().lower())

def flip_name_format(name):
    # "Last, First" -> "First Last"
    try:
        last, first = name.split(", ")
        return f"{first} {last}"
    except Exception:
        return name

def fuzzy_match(a, b):
    return difflib.SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

def get_play_by_play(game_pk, cache):
    if game_pk in cache:
        return cache[game_pk]
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/playByPlay"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    cache[game_pk] = data
    return data

def find_best_pitch(row, play_by_play_json):
    target_pitch_number = row["pitch_number"]
    target_pitch_type = str(row["pitch_type"]).upper()
    target_name = flip_name_format(row["name"])
    # Gather all candidate pitches
    candidates = []
    for play in play_by_play_json.get('allPlays', []):
        pitcher_info = play.get("matchup", {}).get("pitcher", {})
        pitcher_name_json = pitcher_info.get("fullName", "")
        for event in play.get("playEvents", []):
            if not event.get("isPitch", False):
                continue
            # Ensure pitchNumber and target_pitch_number are both ints
            try:
                if int(event.get("pitchNumber")) != int(target_pitch_number):
                    continue
            except Exception:
                continue
            # Check pitch_type
            pitch_type_json = event.get("details", {}).get("type", {}).get("code", "")
            if str(pitch_type_json).upper() != target_pitch_type:
                continue
            # Fuzzy match pitcher name
            if fuzzy_match(target_name, pitcher_name_json) < 0.85:
                continue
            candidates.append((event, pitcher_name_json))
    if not candidates:
        return None

    # Prepare features for distance calculation
    row_features = []
    available_features = []
    for csv_f, json_f in zip(CSV_FEATURES, JSON_FEATURES):
        if pd.notna(row[csv_f]):
            row_features.append(row[csv_f])
            available_features.append(json_f)
    if not available_features:
        return candidates[0][0]  # Just return the first if no features to compare

    pitch_features = []
    valid_candidates = []
    for event, _ in candidates:
        features = []
        for json_f in available_features:
            features.append(event.get('pitchData', {}).get(json_f, np.nan))
        if not any(pd.isna(f) for f in features):
            pitch_features.append(features)
            valid_candidates.append(event)
    if not pitch_features:
        return candidates[0][0]  # fallback

    dists = euclidean_distances([row_features], pitch_features)
    min_idx = np.argmin(dists)
    return valid_candidates[min_idx]

def get_playId_from_pitch(pitch_event):
    return pitch_event.get('playId')

# Load your dataset
df = pd.read_csv("pitcher_verified_ids_with_gamepk_pitchnum.csv")

cache = {}
df["final_working_URL"] = None

chunk_size = 100
for start in range(0, len(df), chunk_size):
    end = min(start + chunk_size, len(df))
    print(f"Processing rows {start} to {end-1}...")
    for idx in range(start, end):
        row = df.iloc[idx]
        game_pk = row.get("game_pk", None)
        pitch_number = row.get("pitch_number", None)
        # Skip rows with missing or invalid game_pk or pitch_number
        if (
            pd.isna(game_pk) or pd.isna(pitch_number) or
            str(game_pk).strip() == "" or str(pitch_number).strip() == "" or
            str(game_pk).strip() == "not found" or str(pitch_number).strip() == "not found"
        ):
            df.at[idx, "final_working_URL"] = None
            continue
        try:
            play_by_play_json = get_play_by_play(str(int(game_pk)), cache)
            best_pitch = find_best_pitch(row, play_by_play_json)
            if best_pitch:
                playId = get_playId_from_pitch(best_pitch)
                if playId:
                    url = f"https://baseballsavant.mlb.com/sporty-videos?playId={playId}"
                    df.at[idx, "final_working_URL"] = url
                else:
                    df.at[idx, "final_working_URL"] = None
            else:
                df.at[idx, "final_working_URL"] = None
        except Exception as e:
            print(f"Error on row {idx}: {e}")
            df.at[idx, "final_working_URL"] = None
    df.to_csv("final_dataset_pitchDNA.csv", index=False)
    print(f"Saved progress through row {end-1}.")

print("✅ All done! Results saved to final_dataset_pitchDNA.csv")

