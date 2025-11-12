from checker import check_api_auth_error
from logger.logger import get_logger
from sessions.session_settings import odds_session

session = odds_session
logger = get_logger(__file__)

URL_ENDPOINT_SPORTS = "/v4/sports/"
URL_ENDPOINT_ODDS = "/v4/sports/{sport}/odds/"
URL_ENDPOINT_SPORTS_SCORES = '/v4/sports/{sport}/scores'
URL_ENDPOINT_EVENTS_HISTORICAL_ODDS = "/v4/historical/sports/{sport}/odds/"


def get_sports():
    res = session.get(URL_ENDPOINT_SPORTS)
    logger.debug(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")

    check_api_auth_error(logger, res.status_code)
    return res.json()


def get_odds(sport_key, regions='us,uk,eu,au', markets='h2h,spreads,totals', oddsFormat='decimal'):
    params = {
        'regions': regions,
        'markets': markets,
        'oddsFormat': oddsFormat
    }
    res = session.get(URL_ENDPOINT_ODDS.format(sport=sport_key), params=params)
    logger.debug(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")

    check_api_auth_error(logger, res.status_code)
    return res.json()


def get_historical_odds_for_datetime(sport_key, date_str, regions='eu,us,uk', markets='h2h,spreads,totals',
                                     odds_format='decimal',
                                     bk='pinnacle,bet365,williamhill,unibet,bwin,1xbet,betsson,coral,ladbrokes'):
    params = {
        'regions': regions,
        'markets': markets,
        'oddsFormat': odds_format,
        'bookmakers': bk,
        'date': date_str,
        'dateFormat': 'iso'
    }

    res = session.get(URL_ENDPOINT_EVENTS_HISTORICAL_ODDS.format(sport=sport_key), params=params)
    logger.debug(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")

    check_api_auth_error(logger, res.status_code)
    data = res.json()
    if isinstance(data, dict) and 'data' in data:
        return data['data']
    return data


def get_completed_matches(sport_key, regions='eu,us,uk', odds_format='decimal',
                          bk='pinnacle,bet365,williamhill,unibet,bwin,1xbet,betsson,coral,ladbrokes'):
    params = {
        'regions': regions,
        'bookmakers': bk,
        'oddsFormat': odds_format
    }

    res = session.get(URL_ENDPOINT_SPORTS_SCORES.format(sport=sport_key), params=params)
    logger.debug(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")

    check_api_auth_error(logger, res.status_code)
    data = res.json()
    logger.debug(data)
    return [match for match in data if match.get('completed') == True]
