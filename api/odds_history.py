import time
from datetime import datetime, timezone, timedelta

import pandas as pd

from logger.logger import get_logger
from routes.odds_routes import get_historical_odds_for_datetime, get_completed_matches
from save_df import save_df_with_cleanup, get_last_save_filename, get_work_dir
from settings import TIME_SNAPSHOTS, ADDITIONAL_SPORTS_COUNT, SLEEP_BETWEEN_CALLS

LOCAL_DIR = get_work_dir("api/data/odds-api/")
logger = get_logger(__file__)

def get_historical_odds(odds_events, target_matches, time_label):
    rows = []
    matched_events = 0
    if not odds_events:
        return rows, matched_events

    target_dict = {}

    for i, row in target_matches.iterrows():
        match_id = row['id']
        target_dict[match_id] = row

    for event in odds_events:
        event_id = event.get('id')
        if event_id not in target_dict:
            continue
        matched_events += 1
        match_data = target_dict[event_id]

        for bookmaker in event.get('bookmakers', []):
            bookmaker_key = bookmaker.get('key', 'unknown')
            bookmaker_title = bookmaker.get('title', 'Unknown')

            for market in bookmaker.get('markets', []):
                market_key = market.get('key')
                for outcome in market.get('outcomes', []):
                    rows.append({
                        'event_id': event_id,
                        'sport_key': match_data['sport_key'],
                        'commence_time': match_data['commence_time'],
                        'home_team': match_data['home_team'],
                        'away_team': match_data['away_team'],
                        'bookmaker_key': bookmaker_key,
                        'bookmaker_title': bookmaker_title,
                        'market': market_key,
                        'outcome_name': outcome.get('name'),
                        'outcome_odds': outcome.get('price'),
                        'point': outcome.get('point', None),
                        'snapshot_time': time_label,
                        'last_update': market.get('last_update'),
                        'collected_at': datetime.now(timezone.utc).isoformat()
                    })

    return rows, matched_events


def process_historical_odds():
    logger.info("Производится обработка исторических событий!")
    existing_odds_df = None

    try:
        existing_odds_df = pd.read_csv(LOCAL_DIR +
                                       get_last_save_filename(logger=logger, name='odds_data_normal', path=LOCAL_DIR))
    except FileNotFoundError:
        logger.error("Для запуска скрипта необходим предварительно сгенерированный файл - odds_data_normal-*.csv")
        return

    already_processed = set()
    if 'sport_key' in existing_odds_df.columns:
      already_collected_sports = set(existing_odds_df['sport_key'].unique())
    else:
      already_collected_sports = set()

    if 'snapshot_time' not in existing_odds_df.columns:
        existing_odds_df['snapshot_time'] = 'default'

    existing_odds_df['temp_date'] = pd.to_datetime(
        existing_odds_df['commence_time']
    ).dt.strftime('%Y-%m-%d')

    for i, row in existing_odds_df.iterrows():
      key = f"{row['sport_key']}_{row['temp_date']}_{row['snapshot_time']}"
      already_processed.add(key)

    completed_matches = []

    for sport_key in already_collected_sports:
        completed_matches.extend(get_completed_matches(sport_key))

    if len(completed_matches) == 0:
        logger.info("Нет завершенных матчей...")
        return

    sport_stats = pd.Series([match['sport_key'] for match in completed_matches]).value_counts()
    if len(sport_stats) == 0:
        logger.info("Нет спортивных данных...")
        return

    target_sports = sport_stats.head(ADDITIONAL_SPORTS_COUNT).index.tolist()

    target_matches = [match for match in completed_matches if match['sport_key'] in target_sports]
    target_matches_df = pd.DataFrame(target_matches)
    target_matches_df['commence_dt'] = pd.to_datetime(target_matches_df['commence_time'])


    requests_to_make = []
    for i, match in target_matches.iterrows():
        commence_dt = match['commence_dt']
        sport_key = match['sport_key']
        date_short = commence_dt.strftime('%Y-%m-%d')

        for snapshot in TIME_SNAPSHOTS:
            target_dt = commence_dt - timedelta(hours=snapshot['hours_before'])
            date_str = target_dt.strftime('%Y-%m-%dT%H:00:00Z')
            time_label = snapshot['label']
            check_key = f"{sport_key}_{date_short}_{time_label}"

            if check_key not in already_processed:
                requests_to_make.append({
                    'sport_key': sport_key,
                    'date_str': date_str,
                    'time_label': time_label,
                    'date_short': date_short,
                    'match_id': match['id']
                })

    if len(requests_to_make) == 0:
        logger.info("Для совершения необходимо - 0 запросов (Конец обработки)")
        return

    requests_df = pd.DataFrame(requests_to_make)

    sport_counters = {}
    round_robin_indices = []
    for i, row in requests_df.iterrows():
        sport = row['sport_key']
        if sport not in sport_counters:
            sport_counters[sport] = 0
        round_robin_indices.append(sport_counters[sport])
        sport_counters[sport] += 1

    requests_df['round_robin_idx'] = round_robin_indices
    requests_df = requests_df.sort_values(['round_robin_idx', 'sport_key']).reset_index(drop=True)
    grouped = list(requests_df.groupby(['sport_key', 'date_str', 'time_label', 'date_short']))

    new_odds_data = []
    matches_by_sport = {}

    for s in target_sports:
        subset = target_matches[target_matches['sport_key'] == s]
        matches_by_sport[s] = subset

    for (sport_key, date_str, time_label, _date_short), _group in grouped:
        try:
            odds_events = get_historical_odds_for_datetime(sport_key, date_str)
            if odds_events:
                sport_matches = matches_by_sport.get(sport_key)
                if sport_matches is not None:
                    odds_rows, _matched =  get_historical_odds(odds_events, sport_matches, time_label)
                    if odds_rows:
                        new_odds_data.extend(odds_rows)
        except Exception as e:
            logger.debug(f"Пропущено событие sport_key={sport_key} - {e}")

        time.sleep(SLEEP_BETWEEN_CALLS)

    if len(new_odds_data) > 0:
        new_odds_df = pd.DataFrame(new_odds_data)
        final_df = pd.concat([existing_odds_df.drop(columns=['temp_date'], errors='ignore'),
                              new_odds_df], ignore_index=True)
        final_df['point'] = final_df['point'].fillna('is not for h2h')
        final_df = final_df.drop('temp_date', axis=1)
        final_df = final_df.drop('bookmaker_key', axis=1)
        final_df = final_df.drop('last_update', axis=1)
        final_df = final_df.drop_duplicates()
        final_df = final_df.reset_index(drop=True)
        save_df_with_cleanup(logger=logger, df=final_df, name="bk_offers_history_normal", path=LOCAL_DIR)
        logger.info(f"Извлечение данных завершено! Добавлено {final_df.shape[0]} строк, {final_df.shape[1]} колонок")


if __name__ == "__main__":
    process_historical_odds()