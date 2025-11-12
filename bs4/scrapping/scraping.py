import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from logger.logger import get_logger

LOCAL_DIR = os.path.join(os.path.dirname(__file__), "data/bk-ratings/")
os.makedirs(LOCAL_DIR, exist_ok=True)
logger = get_logger(__file__)

top_10_best = {
    1: "https://bookmaker-ratings.ru/author/badostips/",
    2: "https://bookmaker-ratings.ru/author/zhukov/",
    3: "https://bookmaker-ratings.ru/author/paveltennis/",
    4: "https://bookmaker-ratings.ru/author/r-gasparyan/",
    5: "https://bookmaker-ratings.ru/author/kuzmichbetting/",
    6: "https://bookmaker-ratings.ru/author/falcao1984/",
    7: "https://bookmaker-ratings.ru/author/valerast/",
    8: "https://bookmaker-ratings.ru/author/vs-seoanalytica/",
    9: "https://bookmaker-ratings.ru/author/shnyakindmitriy/",
    10: "https://bookmaker-ratings.ru/author/adebayor/"
}

top_10_average = {
    1: "https://bookmaker-ratings.ru/author/aroyan/",
    2: "https://bookmaker-ratings.ru/author/thomas/",
    3: "https://bookmaker-ratings.ru/author/chatgpttips/",
    4: "https://bookmaker-ratings.ru/author/denisnalivayko/",
    5: "https://bookmaker-ratings.ru/author/perkaniuks/",
    6: "https://bookmaker-ratings.ru/author/nigmatullin/",
    7: "https://bookmaker-ratings.ru/author/ilvyacheslavepta/",
    8: "https://bookmaker-ratings.ru/author/rb_176780/",
    9: "https://bookmaker-ratings.ru/author/vladrad/",
    10: "https://bookmaker-ratings.ru/author/lawrenson/"
}

top_10_worst = {
    1: "https://bookmaker-ratings.ru/author/arturio/",
    2: "https://bookmaker-ratings.ru/author/ministrelia96/",
    3: "https://bookmaker-ratings.ru/author/etitov/",
    4: "https://bookmaker-ratings.ru/author/paruyr/",
    5: "https://bookmaker-ratings.ru/author/andronov/",
    6: "https://bookmaker-ratings.ru/author/dmitrii-m/",
    7: "https://bookmaker-ratings.ru/author/kgenich/",
    8: "https://bookmaker-ratings.ru/author/dkazansky/",
    9: "https://bookmaker-ratings.ru/author/lovchev/",
    10: "https://bookmaker-ratings.ru/author/kazakov/"
}

def to_html(data_dict, folder="soups"):
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 45)
    answer = []
    for i in range(1, 11):
        url = data_dict[i]
        driver.get(url)
        try:
            ended_predicts_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                                           ".whitespace-nowrap.pr-2.pr-4")))
            ended_predicts_button.click()
        except:  # тут ловит ожидание > 60 сек значит прерывает итерацию если не может нажать кнопку
            continue

        c = 0
        while True:
            c += 1
            if c > 400:
                break
            show_more = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Смотреть еще']")))
            previous_count = len(driver.find_elements(By.CSS_SELECTOR,
                                                      ".select-none.text-md.text-blue-400.block.cursor-pointer"
                                                      ".rounded-2xl.bg-white.p-3.shadow-gray-300.mb-2"))
            show_more.click()
            time.sleep(0.2)
            try:
                wait.until(lambda d: len(
                    d.find_elements(By.CSS_SELECTOR,
                                    ".select-none.text-md.text-blue-400.block.cursor-pointer.rounded-2xl.bg-white.p-3"
                                    ".shadow-gray-300.mb-2")) > previous_count)
            except: #тут ловит ожидание > 60 сек значит прерывает итерацию.
                break

        html_content = driver.page_source

        soup = BeautifulSoup(html_content, 'html.parser')
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        with open(f"{folder}/{folder}_{i}.html", "w", encoding="utf-8") as f:
            f.write(html_content)
            logger.info(f"Сохранено: {folder}/{folder}_{i}.html")
        answer.append(soup)
    driver.quit()
    return answer


def parser():
    to_html(top_10_best, folder=LOCAL_DIR + "temp_best")
    to_html(top_10_worst, folder=LOCAL_DIR + "temp_worst")
    to_html(top_10_average, folder=LOCAL_DIR + "temp_average")


if __name__ == "__main__":
    parser()