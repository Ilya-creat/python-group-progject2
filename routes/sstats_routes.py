from checker import check_api_auth_error
from logger.logger import get_logger
from sessions.session_settings import sstats_session

session = sstats_session
logger = get_logger(__file__)

URL_ENDPOINT_GAMES_LIST = "/Games/list"
URL_ENDPOINT_ODDS = "/Odds/{id}"


def get_games_list(league_id, year, last):
    response = session.get(URL_ENDPOINT_GAMES_LIST, params={
        "leagueid": league_id,
        "year": year
    }) if last is None else session.get(URL_ENDPOINT_GAMES_LIST, params={
        "leagueid": league_id,
        "year": year,
        "from": last
    })

    check_api_auth_error(logger, response.status_code)
    return response.json()['data']


def get_odds(id_odds):
    response = session.get(URL_ENDPOINT_ODDS.format(id=id_odds))

    check_api_auth_error(logger, response.status_code)
    return response.json()['data']
