from logger.logger import get_logger
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime

logger = get_logger(__file__)

API_KEY = 'Murad_API'
BASE_URL = 'https://api.the-odds-api.com/v4'

all_data = []
def get_sports():
    url = f'{BASE_URL}/sports'
    res = requests.get(url, params={'apiKey': API_KEY})
    print(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")
    return res.json()

def get_odds(sport_key, regions='us,uk,eu,au', markets='h2h,spreads,totals', oddsFormat='decimal'):
    url = f'{BASE_URL}/sports/{sport_key}/odds'
    params = {
        'apiKey': API_KEY,
        'regions': regions,
        'markets': markets,
        'oddsFormat': oddsFormat
    }
    res = requests.get(url, params=params)
    print(f"Осталось запросов: {res.headers.get('x-requests-remaining', 'N/A')}")
    return res.json()

print("Получаем список видов спорта...")
sports = get_sports()
print(f"Найдено видов спорта: {len(sports)}")

active_sports = [s for s in sports if s.get('active', False)]
print(f"Активных видов спорта: {len(active_sports)}")

for idx, sport in enumerate(active_sports):
    sport_key = sport['key']
    sport_title = sport['title']
    
    print(f"\n[{idx+1}/{len(active_sports)}] Обрабатываем: {sport_title} ({sport_key})")
    
    try:
        odds_data = get_odds(sport_key)
        
        if not odds_data:
            print(f"Нет данных для {sport_title}")
            continue
        
        print(f"Найдено событий: {len(odds_data)}")
        
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
        
        print(f"Собрано строк: {len(all_data)}")
        
        time.sleep(1)
        
    except Exception as e:
        print(f"Ошибка при обработке {sport_title}: {str(e)}")
        continue

df = pd.DataFrame(all_data)

print(df.head(10))

print(df.info())

#df.to_csv('odds_data.csv', index=False, encoding='utf-8')
#df


#--------------------------------------------------------------
# ПРОВЕРЯЕМ ЗАПОЛНЕНИЯ NaN ДЛЯ h2h
df = pd.read_csv('odds_data.csv', encoding='utf-8')
#print(df.isnull().sum())

df.loc[df['market'] == 'h2h', 'point'] = 0
print("Проверка заполнения:")
print(df[df['market'] == 'h2h']['point'].unique())
print(df[df['market'] != 'h2h']['point'].isnull().sum())
#nan_rows = df[df.isnull().any(axis=1)]
#print(nan_rows)

df.loc[df['market'] == 'h2h_lay', 'point'] = 0
#print(df.isnull().sum())

df.to_csv('odds_data_new.csv', index=False, encoding='utf-8')

#--------------------------------------------------------------
# БЕРЕМ ИНФУ О ДАТАФРЕЙМЕ
print(df.info())
print('\n', df.head())

print('\nОписательные статистики по числовым столбцам:')
print(df.describe())

#--------------------------------------------------------------
# ДОБАВЛЯЕМ НОВЫЕ КАТЕГОРИИ
def is_min(x):
    return x == x.min()

def is_max(x):
    return x == x.max()

df['is_favorite'] = np.nan
df['is_underdog'] = np.nan

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

df.to_csv('odds_data_new_favund.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    pass
