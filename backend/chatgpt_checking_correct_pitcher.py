import pandas as pd
import requests
import time
import json
import difflib
import re
from unidecode import unidecode
import os

pd.DataFrame({"a": [1,2,3]}).to_csv("test_save.csv", index=False)

# Load your dataset
df = pd.read_csv("pitcher_long_format_with_umap_with_ids_and_working_urls.csv")

# Ensure the column exists
df["correct_pitcher_match"] = None

def normalize_name(name):
    return unidecode(name.strip().lower())

def flip_name_format(name):
    """Convert 'Last, First' to 'First Last'."""
    try:
        last, first = name.split(", ")
        return f"{first} {last}"
    except:
        return name

def get_play_data(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/playByPlay"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["allPlays"]
        else:
            return None
    except Exception as e:
        print(f"❌ Failed to fetch game {game_pk}: {e}")
        return None

def find_pitcher_name_by_play_id(plays, target_play_id):
    # Search all playEvents in allPlays for the matching playId
    for play in plays:
        for event in play.get("playEvents", []):
            if event.get("playId") == target_play_id:
                pitcher = play.get("matchup", {}).get("pitcher", {})
                return pitcher.get("fullName")
    return None

def extract_game_pk(savant_url):
    # Handles URLs like ...playId=447995-8
    m = re.search(r'playId=(\d+)-', str(savant_url))
    if m:
        return m.group(1)
    return None

def extract_playId(correct_savant_url):
    # Extracts playId from the savant_url
    m = re.search(r'playId=([a-f0-9\-]+)', str(correct_savant_url))
    if m:
        return m.group(1)
    return None

df = df.reset_index(drop=True)

for idx in range(2234, len(df)):
    row = df.iloc[idx]
    print(f"🔍 Checking row {idx}...")

    try:
        savant_url = row["correct_savant_url"]
        if pd.isna(savant_url) or "playId=" not in savant_url:
            df.at[idx, "correct_pitcher_match"] = False
            continue

        # Extract playId and game_pk
        play_id = extract_playId(row["correct_savant_url"])
        game_pk = extract_game_pk(row["savant_url"])
        print(f"Extracted game_pk: {game_pk}, play_id: {play_id}")

        if not game_pk or not play_id:
            df.at[idx, "correct_pitcher_match"] = False
            continue

        plays = get_play_data(game_pk)
        if not plays:
            df.at[idx, "correct_pitcher_match"] = False
            continue

        pitcher_api_name = find_pitcher_name_by_play_id(plays, play_id)
        if not pitcher_api_name:
            df.at[idx, "correct_pitcher_match"] = False
            continue

        pitcher_api_name = normalize_name(pitcher_api_name)
        dataset_name = normalize_name(flip_name_format(row["name"]))

        match_ratio = difflib.SequenceMatcher(None, pitcher_api_name, dataset_name).ratio()
        print(f"Comparing: '{pitcher_api_name}' vs '{dataset_name}' (ratio: {match_ratio})")
        df.at[idx, "correct_pitcher_match"] = match_ratio > 0.75

    except Exception as e:
        print(f"🔥 Error on row {idx}: {e}")
        df.at[idx, "correct_pitcher_match"] = False

    if (idx - 2234) % 100 == 0:
        print(f"💾 Saving progress at row {idx}...")
        df.to_csv("/Users/cesarpena/Documents/Pitcher_Stats/pitcher_long_format_with_validated_pitchers_partial.csv", index=False)
        

# Final save
df.to_csv("pitcher_long_format_with_validated_pitchers.csv", index=False)
print("✅ Done! Full file saved.")
print("Current working directory:", os.getcwd())

