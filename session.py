from __future__ import annotations

from logger.logger import get_logger
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = get_logger(__file__)


def create_session(base_url: str,
                   extra_headers: dict | None = None,
                   use_ssl: bool = True,
                   params: dict | None = None) -> Session:
    """
    Реализация сессии для подключения
    """

    session = Session()

    headers = {
        "Accept": "application/json",
        "User-Agent": "Windows 98/1.0",
    }

    if extra_headers:
        headers.update(extra_headers)

    session.headers.update(headers)

    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    adapter = HTTPAdapter(max_retries=retry)

    session.mount("https://", adapter)
    session.verify = use_ssl

    session_method = session.request

    def request_(method, url, *args, **kwargs):
        url = url if url.startswith("http") else f"{base_url.rstrip('/')}/{url.lstrip('/')}"

        if params is not None:
            kw_params = kwargs.get("params", {})
            kw_params.update(params)
            kwargs["params"] = kw_params

        logger.info(f"{method.upper()} -> {url}; {kwargs}")

        return session_method(method, url, *args, **kwargs)

    session.request = request_

    return session
