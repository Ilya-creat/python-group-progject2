import os
from session import create_session
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")

odds_session = create_session(base_url="https://api.the-odds-api.com",
                              params={"apiKey": ODDS_API_KEY})
