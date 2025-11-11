import os
from dotenv import load_dotenv

load_dotenv()

logging_set_level = os.getenv("LOGGER_LEVEL", "20")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
SSTATS_API_KEY = os.getenv("SSTATS_API_KEY")

LIMIT_QUERY_ODDS_V4_SPORTS = None
SLEEP_BETWEEN_CALLS = 0.5
TIME_SNAPSHOTS = [
    {'hours_before': 24, 'label': '24h_before'},
    {'hours_before': 12, 'label': '12h_before'},
    {'hours_before': 4,  'label': '4h_before'},
    {'hours_before': 1,  'label': '1h_before'},
]
ADDITIONAL_SPORTS_COUNT = 3