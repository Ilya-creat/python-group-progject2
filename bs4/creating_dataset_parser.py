import pandas as pd
from bs4 import BeautifulSoup

from logger.logger import get_logger
from save_df import save_df_with_cleanup, get_work_dir

df = pd.DataFrame(columns=[
    "Name", "ROI", "Place_in_top", "Predicted_outcome",
    "Coefficient", "Outcome", "Team1", "Team2", "League", "Date",
])

LOCAL_DIR = get_work_dir("data/bk-ratings/")
logger = get_logger(__file__)


def create_dataset_from_html(html_doc, place):
    with open(f"{html_doc}", "r", encoding="utf-8") as f:
        average = f.read()
    soup = BeautifulSoup(average, "html.parser")

    name = soup.find("h1", class_="text-h3")
    name = name.text.strip() if name else None
    parent_div = soup.find('div',
                           class_='pl-4 m-lg:pl-5 d-md:pl-1.5 flex touch-pan-y select-none items-start overflow-hidden '
                                  'transition-all h-full will-change-transform scrollbar-none scrollbar-h-0 t-lg:'
                                  'overflow-x-scroll pt-4 mr-5 d-sm:mr-7 pb-1')

    roi = parent_div.find('div', string=lambda t: 'ROI' in t)
    roi = roi.text.strip() if roi else None
    place_in_top = place

    for predict in soup.find_all("a",
                                 class_="select-none text-md text-blue-400 block cursor-pointer rounded-2xl bg-white "
                                        "p-3 shadow-gray-300 mb-2"):
        check = predict.find("use", href="/static/sprite-group/sport-types.svg#football")
        if not check:
            continue

        parent_pred_block = predict.select_one(
            "div.flex.w-full.items-center.justify-between.rounded-xl.bg-gray-80.py-2.pl-3.pr-2"
            ".m-lg\\:mt-3.d-lg\\:ml-3.d-lg\\:mt-0"
        )
        predicted_outcome = None
        if parent_pred_block:
            predicted_outcome = parent_pred_block.select_one(
                "div.text-md.font-bold.leading-4.text-gray-600:not(.lowercase)")
            predicted_outcome = predicted_outcome.text.strip() if predicted_outcome else None

        coefficient = predict.find("div", class_="text-md font-bold leading-4 text-gray-700")
        coefficient = coefficient.text.strip() if coefficient else None

        parent_outcome_block = predict.find("div", class_="flex items-center justify-between")
        outcome = None
        if parent_outcome_block:
            outcome_tag = parent_outcome_block.find("div", class_=["text-md", "leading-5"])
            if outcome_tag:
                classes = outcome_tag.get("class", [])
                if "text-green-500" in classes:
                    outcome = 1
                elif "text-red-500" in classes:
                    outcome = 0
                else:
                    outcome = None

        team1 = predict.select_one(".block.m-lg\\:hidden div:nth-child(1)").text.strip()
        team2 = predict.select_one(".block.m-lg\\:hidden div:nth-child(2)").text.strip()

        date = predict.select_one("div.text-gray-300.text-sm span")
        date = date.text.strip() if date else None
        if (not date) or ("Сегодня" in date) or ("Вчера" in date):
            continue
        months = {
            "Янв": 1, "Фев": 2, "Мар": 3, "Апр": 4, "Май": 5, "Мая": 5, "Июн": 6, "Июнь": 6,
            "Июл": 7, "Июля": 7, "Авг": 8, "Августа": 8, "Сен": 9, "Сент": 9, "Окт": 10, "Октября": 10,
            "Ноя": 11, "Ноября": 11, "Дек": 12, "Декабря": 12
        }
        s = date.split(",")[0].split()
        day = int(s[0])
        month = months[s[1]]
        year = int(s[2]) if len(s) > 2 and s[2].isdigit() else 2025
        date = f"{year:04d}-{month:02d}-{day:02d}"

        league = predict.select_one(
            "div.max-w-40.overflow-hidden.text-ellipsis.whitespace-nowrap.text-sm.text-gray-300.m-md\\:max-w-50")
        league = league.text.strip() if league else None

        df.loc[len(df)] = {
            "Name": name,
            "ROI": roi,
            "Place_in_top": place_in_top,
            "Predicted_outcome": predicted_outcome,
            "Coefficient": coefficient,
            "Outcome": outcome,
            "Team1": team1,
            "Team2": team2,
            "League": league,
            "Date": date,
        }


def generate_db():
    global df
    folders = ['temp_worst']

    for folder in folders:
        for i in range(1, 11):
            if folder == 'top_worst':
                create_dataset_from_html(f'{LOCAL_DIR}{folder}/{folder}_{i}.html', 132 + i)
            elif folder == 'top_best':
                create_dataset_from_html(f'{LOCAL_DIR}{folder}/{folder}_{i}.html', i)
            else:
                create_dataset_from_html(f'{LOCAL_DIR}{folder}/{folder}_{i}.html', i + 64)

    df = df.dropna(subset=['Team1', 'Team2', 'Outcome', 'Predicted_outcome']).reset_index(drop=True)
    df['League'] = df['League'].fillna('Неизвестная лига')
    df['ROI'] = df['ROI'].str.replace(r'[^-0-9.]', '', regex=True).astype(float)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.drop_duplicates()
    df = df.reset_index(drop=True)

    df['Prediction_Size'] = df.groupby('Name').transform('size')
    df['Right_Predictions'] = df.groupby('Name')['Outcome'].transform('sum')
    df = df.sort_values('Prediction_Size').reset_index(drop=True)
    df['Date'] = pd.to_datetime(df['Date'])

    df['Avg_Predictions_Per_Day'] = df.groupby('Name')['Prediction_Size'].transform(
        lambda s: s / max((df.loc[s.index, 'Date'].max() - df.loc[s.index, 'Date'].min()).days, 1)
    )

    df = df.dropna().reset_index(drop=True)
    save_df_with_cleanup(logger=logger, df=df, name="experts_top", path=LOCAL_DIR)


if __name__ == "__main__":
    generate_db()
