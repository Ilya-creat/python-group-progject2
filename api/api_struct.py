import os
import time

import requests

from logger.logger import get_logger
from datetime import datetime

import pandas as pd

from save_df import save_with_cleanup
from settings import stats_session

LOCAL_DIR = os.path.join(os.path.dirname(__file__), "data/odds/")
os.makedirs(LOCAL_DIR, exist_ok=True)
logger = get_logger(__file__)

def parsing_from_api_matches():
    f_list = []
    for league_id in range(1, 1207):
        for year in range(2024, 2026):
            url = f'https://api.sstats.net//Games/list?leagueid={league_id}&year={year}&ended=true'
            try:
                temp_page = stats_session.get(url)
                temp_page.raise_for_status()
                temp_page = temp_page.json()
                if temp_page['status'] == 'OK':
                    temp_df = pd.DataFrame(temp_page['data'])
                    f_list.append(temp_df)
                    print('Norm')
            except Exception as e:
                if isinstance(e,
                              requests.exceptions.HTTPError) and e.response is not None and e.response.status_code == 429:
                    print('Too Many Requests, starting cycle')
                    for i in range(20):
                        time.sleep(3)
                        try:
                            temp_page = stats_session.get(url)
                            temp_page.raise_for_status()
                            temp_page = temp_page.json()
                            if temp_page['status'] == 'OK':
                                temp_df = pd.DataFrame(temp_page['data'])
                                f_list.append(temp_df)
                                print('Norm после 429')
                                break
                        except Exception as e2:
                            print(f'Ошибка после повтора: {e2}')
                            continue
                else:
                    print(f'Ошибка {e}')
                    time.sleep(2)
                    continue
    df_matches = pd.concat(f_list, ignore_index=True)
    return save_with_cleanup(logger=logger, df=df_matches, path=LOCAL_DIR, name="df_matches")

def parsing_from_api_odds(df_matches):
    df_for_ids = pd.read_csv(f'{df_matches}')
    ids = df_for_ids['id'].unique().tolist()
    rows = []
    for id in ids:
        url = f'https://api.sstats.net/Odds/{id}'
        try:
            response = stats_session.get(url)
            response.raise_for_status()
            data = response.json().get('data', [])
            if not data:
                continue
            for bookmaker in data:
                row = {
                    'MatchId': id,
                    'bookmakerName': bookmaker['bookmakerName']
                }
                for market in bookmaker['odds']:
                    if market['marketName'] == 'Match Winner':
                        for odd in market['odds']:
                            row[f"Match Winner_{odd['name']}"] = odd['value']
                rows.append(row)
            print('Norm')
        except Exception as e:
            if isinstance(e,
                          requests.exceptions.HTTPError) and e.response is not None and e.response.status_code == 429:
                print('Too Many Requests, starting cycle')
                for i in range(20):
                    time.sleep(3)
                    try:
                        response = stats_session.get(url)
                        response.raise_for_status()
                        data = response.json().get('data', [])
                        for bookmaker in data:
                            row = {
                                'MatchId': id,
                                'bookmakerName': bookmaker['bookmakerName']
                            }
                            for market in bookmaker['odds']:
                                if market['marketName'] == 'Match Winner':
                                    for odd in market['odds']:
                                        row[f"Match Winner_{odd['name']}"] = odd['value']
                            rows.append(row)
                        print('Norm after 429')
                    except Exception as e2:
                        print(f'Ошибка после повтора: {e2}')
                        continue
            else:
                print(f'Ошибка {e}')
                time.sleep(2)
                continue