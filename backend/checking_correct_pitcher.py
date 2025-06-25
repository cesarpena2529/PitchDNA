import pandas as pd
import requests
import re
from rapidfuzz import fuzz

def extract_game_pk(savant_url):
    # Extracts numbers before the dash in playId=447995-8
    m = re.search(r'playId=(\d+)-\d+', str(savant_url))
    if m:
        return m.group(1)
    return None

def extract_pitch_number(savant_url):
    # Extracts the number after the dash in playId=447995-8
    m = re.search(r'playId=\d+-(\d+)', str(savant_url))
    if m:
        return m.group(1)
    return None

def extract_playId(correct_savant_url):
    # Extracts the UUID after playId= in correct_savant_url
    m = re.search(r'playId=([a-f0-9\-]+)', str(correct_savant_url))
    if m:
        return m.group(1)
    return None

def get_pitcher_name_from_json(game_pk, playId):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/playByPlay"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        for play in data.get("allPlays", []):
            if play.get("playId") == playId:
                pitcher = play.get("matchup", {}).get("pitcher", {})
                return pitcher.get("fullName", None)
    except Exception as e:
        print(f"Error fetching or parsing JSON for game_pk={game_pk}: {e}")
    return None

def fuzzy_match_name(dataset_name, json_name):
    if not dataset_name or not json_name:
        return False
    dataset_name = dataset_name.lower().replace(",", "")
    json_name = json_name.lower()
    score1 = fuzz.token_sort_ratio(dataset_name, json_name)
    score2 = fuzz.token_sort_ratio(json_name, dataset_name)
    return max(score1, score2) > 85

df = pd.read_csv("pitcher_long_format_with_umap_with_ids_and_working_urls.csv")

# If resuming, load previous results if present
if "correct_pitcher_url" in df.columns:
    results = df["correct_pitcher_url"].tolist()
else:
    results = [None] * len(df)

start_row = 2236

for idx in range(start_row, len(df)):
    row = df.iloc[idx]
    savant_url = row.get("savant_url", "")
    correct_savant_url = row.get("correct_savant_url", "")
    dataset_name = row.get("name", "")
    game_pk = extract_game_pk(savant_url)
    playId = extract_playId(correct_savant_url)
    print(f"Row {idx}: game_pk={game_pk}, playId={playId}, dataset_name={dataset_name}")
    if not game_pk or not playId:
        print("  Missing game_pk or playId")
        results[idx] = False
    else:
        json_pitcher_name = get_pitcher_name_from_json(game_pk, playId)
        print(f"  JSON pitcher name: {json_pitcher_name}")
        is_correct = fuzzy_match_name(dataset_name, json_pitcher_name)
        print(f"  Fuzzy match: {is_correct}")
        results[idx] = is_correct
    # Save every 100 rows
    if (idx + 1) % 100 == 0:
        df["correct_pitcher_url"] = results
        df.to_csv("pitcher_long_format_with_umap_with_ids_and_working_urls_checked.csv", index=False)
        print(f"Saved progress at row {idx + 1}")

# Final save
df["correct_pitcher_url"] = results
df.to_csv("pitcher_long_format_with_umap_with_ids_and_working_urls_checked.csv", index=False)
print("Done and saved final results.")