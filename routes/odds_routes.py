from logger.logger import get_logger
from settings import odds_session

session = odds_session
logger = get_logger(__file__)

URL_ENDPOINT_SPORTS = "/v4/sports/"
URL_ENDPOINT_ODDS = "/v4/sports/{sport}/odds/"
URL_ENDPOINT_POINTS = "/v4/sports/{sport}/scores/"
URL_ENDPOINT_EVENTS = "/v4/sports/{sport}/events/"
URL_ENDPOINT_EVENTS_ODDS = "/v4/sports/{sport}/events/{eventId}/odds/"
URL_ENDPOINT_EVENTS_MARKETS = "/v4/sports/{sport}/events/{eventId}/markets/"
URL_ENDPOINT_EVENTS_PARTICIPANTS = "v4/sports/{sport}/participants/"
URL_ENDPOINT_EVENTS_HISTORICAL_ODDS = "/v4/historical/sports/{sport}/odds/"
URL_ENDPOINT_EVENTS_HISTORICAL_EVENTS = " /v4/historical/sports/{sport}/events/"
URL_ENDPOINT_EVENTS_HISTORICAL_EVENTS_ODDS = "/v4/historical/sports/{sport}/events/{eventId}/odds"


def get_example_request():
    logger.debug("TEST")
    return session.get("/v4/sports")
