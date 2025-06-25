import pandas as pd
import requests

# Load your CSV
df = pd.read_csv("pitcher_long_format_with_umap_with_ids_and_urls.csv")

# Check only the first 500 rows
urls = df['savant_url'].dropna().head(500)

working_count = 0
for url in urls:
    try:
        resp = requests.get(url, timeout=10)
        if "No Video Found" not in resp.text.lower():
            working_count += 1
    except Exception as e:
        print(f"Error checking {url}: {e}")

print(f"Out of the first 500 URLs, {working_count} appear to work.")