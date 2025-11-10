import os
from dotenv import load_dotenv
from sessions.session import create_session

load_dotenv()

logging_set_level = os.getenv("LOGGER_LEVEL", "20")

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
SSTATS_API_KEY = os.getenv("SSTATS_API_KEY")

LIMIT_QUERY_ODDS_V4_SPORTS = 2

odds_session = create_session(base_url="https://api.the-odds-api.com",
                              params={"apiKey": ODDS_API_KEY})
stats_session = create_session(base_url='https://api.sstats.net',
                               extra_headers={'Authorization': f'ApiKey {SSTATS_API_KEY}'})
