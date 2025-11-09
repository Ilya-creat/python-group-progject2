class UnauthorizedError(Exception):
    pass


def check_api_auth_error(logger, status_code):
    if status_code == 401:
        logger.error("Ошибка 401: Неавторизованный доступ.")
        raise UnauthorizedError("401 Unauthorized — требуется обновить токен или авторизацию.")
