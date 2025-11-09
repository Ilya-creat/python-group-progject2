import os
import time

from logger.logger import get_logger
from datetime import datetime

import pandas as pd
import numpy as np

from routes.odds_routes import get_sports, get_odds
from save_df import save_with_cleanup
from settings import LIMIT_QUERY_ODDS

LOCAL_DIR = os.path.join(os.path.dirname(__file__), "data/odds-api/")
os.makedirs(LOCAL_DIR, exist_ok=True)
logger = get_logger(__file__)


def parsing_from_api():
    all_data = []
    sports = get_sports()
    logger.info(f"Найдено видов спорта: {len(sports)}")

    active_sports = [s for s in sports if s.get('active', False)]
    logger.info(f"Активных видов спорта: {len(active_sports)}")

    def add_odds_data(idx, sport):
        sport_key = sport['key']
        sport_title = sport['title']

        logger.debug(f"\n[{idx + 1}/{len(active_sports)}] Обрабатываем: {sport_title} ({sport_key})")

        try:
            odds_data = get_odds(sport_key)

            if not odds_data:
                logger.debug(f"Нет данных для {sport_title}")
                return

            logger.debug(f"Найдено событий: {len(odds_data)}")

            for event in odds_data:
                event_id = event.get('id')
                home_team = event.get('home_team')
                away_team = event.get('away_team')
                commence_time = event.get('commence_time')

                for bookmaker in event.get('bookmakers', []):
                    bookmaker_key = bookmaker.get('key')
                    bookmaker_title = bookmaker.get('title')
                    last_update = bookmaker.get('last_update')

                    for market in bookmaker.get('markets', []):
                        market_key = market.get('key')

                        for outcome in market.get('outcomes', []):
                            outcome_name = outcome.get('name')
                            odds_value = outcome.get('price')
                            point = outcome.get('point', None)

                            all_data.append({
                                'sport_key': sport_key,
                                'sport_title': sport_title,
                                'event_id': event_id,
                                'home_team': home_team,
                                'away_team': away_team,
                                'commence_time': commence_time,
                                'bookmaker_key': bookmaker_key,
                                'bookmaker_title': bookmaker_title,
                                'market': market_key,
                                'outcome_name': outcome_name,
                                'odds': odds_value,
                                'point': point,
                                'last_update': last_update,
                                'collected_at': datetime.now().isoformat()
                            })
            logger.debug(f"Собрано строк: {len(all_data)}")
        except Exception as e:
            logger.warning(f"Ошибка при обработке {sport_title}: {str(e)}")

    for idx, sport in enumerate(active_sports):
        if (LIMIT_QUERY_ODDS is not None and idx < LIMIT_QUERY_ODDS) or LIMIT_QUERY_ODDS is None:
            add_odds_data(idx, sport)
            time.sleep(3)

    df = pd.DataFrame(all_data)
    return save_with_cleanup(logger=logger, df=df, path=LOCAL_DIR, name="odds_data")


def normalized_df(filename):
    df = pd.read_csv(LOCAL_DIR + filename, encoding='utf-8')
    df.loc[df['market'] == 'h2h', 'point'] = 0
    df.loc[df['market'] == 'h2h_lay', 'point'] = 0

    def is_min(x):
        return x == x.min()

    def is_max(x):
        return x == x.max()

    df['is_favorite'] = np.nan
    df['is_underdog'] = np.nan

    df['is_favorite'] = df['is_favorite'].astype('boolean')
    df['is_underdog'] = df['is_underdog'].astype('boolean')

    mask_h2h = (df['market'] == 'h2h')
    mask_outcomes = (df['outcome_name'].str.lower() != 'draw')
    update_mask = mask_h2h & mask_outcomes

    df.loc[update_mask, 'is_favorite'] = (
        df[update_mask]
        .groupby(['event_id', 'market', 'bookmaker_key'])['odds']
        .transform(is_min)
    )

    df.loc[update_mask, 'is_underdog'] = (
        df[update_mask]
        .groupby(['event_id', 'market', 'bookmaker_key'])['odds']
        .transform(is_max)
    )

    df.loc[df['outcome_name'].str.lower() == 'draw', ['is_favorite', 'is_underdog']] = np.nan
    save_with_cleanup(logger=logger, df=df, path=LOCAL_DIR, name="odds_data_normal")


if __name__ == "__main__":
    logger.info("Запускаем процесс парсинга и нормализации данных [ODDS]")
    normalized_df(parsing_from_api())
