from sessions.session import create_session
from settings import ODDS_API_KEY

odds_session = create_session(base_url="https://api.the-odds-api.com",
                              params={"apiKey": ODDS_API_KEY})
