import glob
import os
from datetime import datetime


def save_with_cleanup(logger, df, path, name, keep_last=5):
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