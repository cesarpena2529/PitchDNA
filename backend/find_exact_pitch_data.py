import pandas as pd
import re
from pybaseball import statcast
from tqdm import tqdm
import random

# Download Statcast data for a week in 2022 (to keep it manageable)
data = statcast(start_dt='2022-06-01', end_dt='2022-06-07')

# Shuffle and select 10 random pitches
sample = data.sample(n=10, random_state=42)

# Show all columns for these 10 pitches
print(sample)

# Save to CSV
sample.to_csv('ten_random_2022_pitches.csv', index=False)

# Print out info to help find the exact pitch
for idx, row in sample.iterrows():
    print(f"Pitch: game_pk={row['game_pk']}, pitch_number={row['pitch_number']}, pitcher_id={row['pitcher']}, date={row['game_date']}")