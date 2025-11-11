import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup

df = pd.DataFrame(columns=[
    "Name", "ROI", "Place_in_top", "Predicted_outcome",
    "Coefficient", "Outcome", "Team1", "Team2", "League", "Date",
])


def create_dataset_from_html(html_doc, place):
    with open(f"{html_doc}", "r", encoding="utf-8") as f:
        average = f.read()
    soup = BeautifulSoup(average, "html.parser")

    name = soup.find("h1", class_="text-h3")
    name = name.text.strip() if name else None
    parent_div = soup.find('div',
                           class_='pl-4 m-lg:pl-5 d-md:pl-1.5 flex touch-pan-y select-none items-start overflow-hidden transition-all h-full will-change-transform scrollbar-none scrollbar-h-0 t-lg:overflow-x-scroll pt-4 mr-5 d-sm:mr-7 pb-1')
    ROI = parent_div.find('div', string=lambda t: 'ROI' in t)
    ROI = ROI.text.strip() if ROI else None
    Place_in_top = place

    for predict in soup.find_all("a",
                                 class_="select-none text-md text-blue-400 block cursor-pointer rounded-2xl bg-white p-3 shadow-gray-300 mb-2"):
        check = predict.find("use", href="/static/sprite-group/sport-types.svg#football")
        if not check:
            continue

        parent_pred_block = predict.select_one(
            "div.flex.w-full.items-center.justify-between.rounded-xl.bg-gray-80.py-2.pl-3.pr-2.m-lg\\:mt-3.d-lg\\:ml-3.d-lg\\:mt-0"
        )
        Predicted_outcome = None
        if parent_pred_block:
            Predicted_outcome = parent_pred_block.select_one(
                "div.text-md.font-bold.leading-4.text-gray-600:not(.lowercase)")
            Predicted_outcome = Predicted_outcome.text.strip() if Predicted_outcome else None

        Coefficient = predict.find("div", class_="text-md font-bold leading-4 text-gray-700")
        Coefficient = Coefficient.text.strip() if Coefficient else None

        parent_outcome_block = predict.find("div", class_="flex items-center justify-between")
        Outcome = None
        if parent_outcome_block:
            outcome_tag = parent_outcome_block.find("div", class_=["text-md", "leading-5"])
            if outcome_tag:
                classes = outcome_tag.get("class", [])
                if "text-green-500" in classes:
                    Outcome = 1
                elif "text-red-500" in classes:
                    Outcome = 0
                else:
                    Outcome = None

        Team1 = predict.select_one(".block.m-lg\\:hidden div:nth-child(1)").text.strip()
        Team2 = predict.select_one(".block.m-lg\\:hidden div:nth-child(2)").text.strip()

        Date = predict.select_one("div.text-gray-300.text-sm span")
        Date = Date.text.strip() if Date else None
        if (not Date) or ("Сегодня" in Date) or ("Вчера" in Date):
            continue
        months = {
            "Янв": 1, "Фев": 2, "Мар": 3, "Апр": 4, "Май": 5, "Мая": 5, "Июн": 6, "Июнь": 6,
            "Июл": 7, "Июля": 7, "Авг": 8, "Августа": 8, "Сен": 9, "Сент": 9, "Окт": 10, "Октября": 10,
            "Ноя": 11, "Ноября": 11, "Дек": 12, "Декабря": 12
        }
        s = Date.split(",")[0].split()
        day = int(s[0])
        month = months[s[1]]
        year = int(s[2]) if len(s) > 2 and s[2].isdigit() else 2025
        Date = f"{year:04d}-{month:02d}-{day:02d}"

        League = predict.select_one(
            "div.max-w-40.overflow-hidden.text-ellipsis.whitespace-nowrap.text-sm.text-gray-300.m-md\\:max-w-50")
        League = League.text.strip() if League else None

        df.loc[len(df)] = {
            "Name": name,
            "ROI": ROI,
            "Place_in_top": Place_in_top,
            "Predicted_outcome": Predicted_outcome,
            "Coefficient": Coefficient,
            "Outcome": Outcome,
            "Team1": Team1,
            "Team2": Team2,
            "League": League,
            "Date": Date,
        }


folders = ['top_best', 'top_average', 'top_worst']

for folder in folders:
    for i in range(1, 11):
        if folder == 'top_worst':
            create_dataset_from_html(f'{folder}_{i}.html', 132 + i)
        elif folder == 'top_best':
            create_dataset_from_html(f'{folder}_{i}.html', i)
        else:
            create_dataset_from_html(f'{folder}_{i}.html', i + 64)

df = df.dropna(subset=['Team1', 'Team2', 'Outcome', 'Predicted_outcome']).reset_index(drop=True)
df['League'] = df['League'].fillna('Неизвестная лига')
# регулярка, приводит к строке, меняет всё что не цифра на пустую строку regex=True показывает что это регулярка а не строка
# обычная .astype(float) приводит в флоат формат
df['ROI'] = df['ROI'].str.replace(r'[^-0-9.]', '', regex=True).astype(float)
df['Date'] = pd.to_datetime(df['Date'])
df = df.drop_duplicates()
df = df.reset_index(drop=True)