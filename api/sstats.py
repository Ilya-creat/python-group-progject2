import ast
import os

import pandas as pd

from logger.logger import get_logger
from routes.sstats_routes import get_games_list, get_odds
from save_df import save_df_with_cleanup, update_df, get_last_save_filename

LOCAL_DIR = os.path.join(os.path.dirname(__file__), "data/sstats-api/")
os.makedirs(LOCAL_DIR, exist_ok=True)
logger = get_logger(__file__)


def generate_matches_noodds(update=False):
    if update:
        logger.info("Запущено обновление данных о матчах")
    else:
        logger.info("Запущенна генерация данных о матчах")

    tmp = []
    latest_game_date = None
    df_matches_last_name = None

    if update:
        df_matches_last_name = get_last_save_filename(logger=logger, path=LOCAL_DIR,
                                                      name="sstats_matches_noodds")
        df_matches_noodds = pd.read_csv(LOCAL_DIR + df_matches_last_name,
                                        encoding='utf-8')
        df_matches_noodds = df_matches_noodds[df_matches_noodds['dateUtc'].notna()].reset_index(drop=True)
        df_matches_noodds = (df_matches_noodds[df_matches_noodds["status"] == 8].sort_values('dateUtc', ascending=False)
                             .reset_index(drop=True))
        latest_game_date = df_matches_noodds.loc[0]['date']

    for league_id in range(1, 1207):
        for year in range(max(2024, int(latest_game_date[:4] if latest_game_date is not None else 0)), 2026):
            data = get_games_list(league_id=league_id, year=year, last=latest_game_date)
            try:
                df_data = pd.DataFrame(data)
                tmp.append(df_data)
            except Exception as e:
                logger.debug(f"gen_matches_noodds() - {e}")

    if update:
        logger.info(f"Обновлению подлежат: {len(tmp)} лиг")
    else:
        logger.info(f"Добавлено: {len(tmp)} лиг")

    df = pd.concat(tmp, ignore_index=True)

    return (save_df_with_cleanup(logger=logger, df=df, path=LOCAL_DIR, name="sstats_matches_noodds") if update is False
            else update_df(logger=logger, df=df, path=LOCAL_DIR, filename=df_matches_last_name)), tmp


def clean_matches_noodds(sstats_matches_noodds_filename):
    logger.info(f"Производится фильтрация и чистка: {sstats_matches_noodds_filename}")

    df = pd.read_csv(LOCAL_DIR + sstats_matches_noodds_filename, encoding='utf-8')
    cols_to_check = ['odds', 'homeFTResult', 'awayFTResult', 'awayResult', 'homeResult', 'roundName', 'elapsed']
    df = df.dropna(subset=cols_to_check).reset_index(drop=True)

    df = df.drop(columns=['periods', 'odds'])

    def safe_literal_eval(val):
        try:
            return ast.literal_eval(val)
        except (ValueError, SyntaxError):
            return None

    df["homeTeam"] = df["homeTeam"].apply(safe_literal_eval)
    df["awayTeam"] = df["awayTeam"].apply(safe_literal_eval)
    df["season"] = df["season"].apply(safe_literal_eval)

    df['homeTeamName'] = df['homeTeam'].apply(lambda x: x['name'])
    df['homeTeamCountry'] = df['homeTeam'].apply(lambda x: x['country']['name'])
    df['awayTeamName'] = df['awayTeam'].apply(lambda x: x['name'])
    df['awayTeamCountry'] = df['awayTeam'].apply(lambda x: x['country']['name'])
    df['leagueName'] = df['season'].apply(lambda x: x['league']['name'])
    df['leagueCountry'] = df['season'].apply(lambda x: x['league']['country']['name'])

    df = df.drop(columns=['homeTeam', 'awayTeam', 'season'])
    df = df.drop_duplicates()

    return save_df_with_cleanup(logger=logger, df=df, path=LOCAL_DIR, name="sstats_matches_noodds_cleaned")


def generate_odds_final(tmp_data, update=False):
    logger.info("Производится извлечение расширенных данных матчей")

    def move_to_row(data, id):
        rows = []
        for bookmaker in data:
            row = {
                'MatchId': id,
                'bookmakerName': bookmaker['bookmakerName']
            }
            for market in bookmaker['odds']:
                if market['marketName'] == 'Match Winner':
                    for odd in market['odds']:
                        if odd['name'] in ['Home', 'Away', 'Draw']:
                            row[f"Match Winner_{odd['name']}"] = odd['value']
            rows.append(row)
        return rows

    ndf = pd.DataFrame(columns=[
        "MatchId",
        "bookmakerName",
        "Match Winner_Home",
        "Match Winner_Draw",
        "Match Winner_Away"
    ])

    filename_df = save_df_with_cleanup(logger=logger, df=ndf, path=LOCAL_DIR, name="sstats_matches_all") \
        if update is False else get_last_save_filename(logger=logger, path=LOCAL_DIR,
                                                       name="sstats_matches_all")

    df_matches_noodds_cleaned_df = pd.concat(tmp_data, ignore_index=True)
    ids = df_matches_noodds_cleaned_df['id'].unique().tolist()
    all_rows = []

    counter = 0

    for idx in ids:
        counter += 1

        try:
            data = get_odds(idx)
            if not data:
                continue
            all_rows.extend(move_to_row(data, idx))

            if counter % 150 == 0:
                logger.info(f"Собрано: {counter} новых данных о матчах")
                filename_df = update_df(logger=logger, df=pd.DataFrame(all_rows), path=LOCAL_DIR, filename=filename_df)
                all_rows = []
                break
        except Exception as e:
            logger.debug(f"generate_odds_final() - {str(e)[:20]}")

    if all_rows:
        filename_df = update_df(logger=logger, df=pd.DataFrame(all_rows), path=LOCAL_DIR, filename=filename_df)

    return filename_df


def clear_odds_final(sstats_matches_all):
    df = pd.read_csv(LOCAL_DIR + sstats_matches_all, encoding="UTF-8")
    df = df.drop_duplicates()
    return save_df_with_cleanup(logger=logger, df=df, path=LOCAL_DIR, name="sstats_matches_all_cleaned")


def resulting_odds(sstats_matches_noodds_cleaned_filename, sstats_matches_all_filename):
    logger.info(f"Производится слияние датасетов: {sstats_matches_noodds_cleaned_filename} "
                f"& {sstats_matches_all_filename}")
    odds_final = pd.read_csv(LOCAL_DIR + sstats_matches_all_filename)
    df_matches_noodds_cleaned = pd.read_csv(LOCAL_DIR + sstats_matches_noodds_cleaned_filename)

    odds_final.rename(columns={'MatchId': 'id'}, inplace=True)
    df_merged = odds_final.merge(df_matches_noodds_cleaned, on='id', how='left')
    df_merged.drop('flashId', axis=1, inplace=True)
    df_merged['extraMinutes'].fillna(0, inplace=True)
    df_merged = df_merged.dropna().reset_index(drop=True)
    df_merged.to_csv('df_merged.csv', index=False)

    save_df_with_cleanup(logger=logger, df=df_merged, path=LOCAL_DIR, name="sstats_data_normal")


if __name__ == "__main__":
    sstats_filename, tmp = generate_matches_noodds()
    df1 = clean_matches_noodds(sstats_filename)
    df2 = clear_odds_final(generate_odds_final(tmp))
    resulting_odds(df1, df2)
