import glob
import os
import shutil
from datetime import datetime
import pandas as pd


def save_df_with_cleanup(logger, df, path, name, keep_last=5):
    """
    Сохраняет DataFrame с меткой времени и удаляет старые версии файлов.

    :param logger: экземпляр логгера файла
    :param df: pandas DataFrame для сохранения
    :param path: путь к папке для сохранения
    :param name: имя файла
    :param keep_last: сколько последних файлов сохранять (по умолчанию 5)
    """

    os.makedirs(path, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{name}-{timestamp}.csv'
    full_path = os.path.join(path, filename)

    df.to_csv(full_path, index=False, encoding='utf-8')
    logger.info(f'DataFrame сохранен: {filename}')

    pattern = os.path.join(path, f'{name}-*.csv')
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)

    if len(files) > keep_last:
        old_files = files[keep_last:]
        for f in old_files:
            os.remove(f)
            logger.info(f'Удален старый  DataFrame: {os.path.basename(f)}')

    return filename


def update_df(logger, df, path, filename, mode='a', header=False):
    """
    Обновляет DataFrame.

    :param logger: экземпляр логгера файла
    :param df: pandas DataFrame для сохранения
    :param path: путь к папке для сохранения
    :param filename: полное имя файла с расширеннием
    :param mode: тип обновления записи
    :param header: имена столбцов
    """

    full_path = os.path.join(path, filename)
    df.to_csv(full_path, mode=mode, header=header, index=False, encoding='utf-8')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = filename.split('-')[0] if '-' in filename else os.path.splitext(filename)[0]
    new_filename = f'{base_name}-{timestamp}.csv'

    new_full_path = os.path.join(path, new_filename)
    old_full_path = os.path.join(path, filename)

    if os.path.exists(old_full_path):
        shutil.copy2(old_full_path, new_full_path)
        os.remove(old_full_path)

    logger.info(f'DataFrame обновлен: {filename} -> {new_filename}')
    return new_filename



def get_last_save_filename(logger, path, name):
    """
    Находит название последнего сохраненного файла по имени и пути.

    :param path: путь к папке, где сохраняются файлы
    :param name: базовое имя файла (без метки времени)
    :return: название последнего файла или None, если файлов нет
    """

    pattern = os.path.join(path, f'{name}-*.csv')
    files = glob.glob(pattern)

    if not files:
        return None

    latest_file = max(files, key=os.path.getmtime)
    logger.info(f'Последний DataFrame: {latest_file}')
    return os.path.basename(latest_file)