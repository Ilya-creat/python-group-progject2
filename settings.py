import os
from dotenv import load_dotenv

load_dotenv()

logging_set_level = os.getenv("LOGGER_LEVEL", "20")  # 10 debug, 20 info, 30 warning, 40 error, 50 critical

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

LIMIT_QUERY_ODDS_V4_SPORTS = 2
