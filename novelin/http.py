from __future__ import annotations

import time
from typing import Any, Optional

import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
RETRY_STATUS = {429, 500, 502, 503, 504}


class HttpError(RuntimeError):
    def __init__(self, message: str, status: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.url = url


class HttpClient:
    def __init__(
        self,
        delay: float = 1.0,
        timeout: float = 30.0,
        retries: int = 3,
        user_agent: Optional[str] = None,
        cookie: Optional[str] = None,
    ) -> None:
        self.delay = max(0.0, delay)
        self.timeout = timeout
        self.retries = max(0, retries)
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent or DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        if cookie:
            self.session.headers["Cookie"] = cookie
        self._last_request = 0.0

    @property
    def has_cookie(self) -> bool:
        return bool(self.cookie)

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def post(
        self,
        url: str,
        data: Optional[Any] = None,
        headers: Optional[dict] = None,
    ) -> requests.Response:
        return self._request("POST", url, data=data, headers=headers)

    def _throttle(self) -> None:
        if self.delay <= 0:
            return
        remaining = self.delay - (time.monotonic() - self._last_request)
        if remaining > 0:
            time.sleep(remaining)

    def _retry_delay(self, attempt: int, response: Optional[requests.Response] = None) -> float:
        if response is not None:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    return max(0.0, float(retry_after))
                except ValueError:
                    pass
        return min(30.0, 2.0 ** attempt)

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        last_error: Optional[Exception] = None

        for attempt in range(self.retries + 1):
            self._throttle()
            try:
                response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(self._retry_delay(attempt))
                    continue
                raise HttpError(f"Gagal menghubungi {url}: {exc}", url=url) from exc
            finally:
                self._last_request = time.monotonic()

            if response.status_code in RETRY_STATUS and attempt < self.retries:
                time.sleep(self._retry_delay(attempt, response))
                continue

            if response.status_code >= 400:
                raise HttpError(
                    f"HTTP {response.status_code} untuk {url}",
                    status=response.status_code,
                    url=url,
                )
            return response

        raise HttpError(f"Gagal menghubungi {url}: {last_error}", url=url)
