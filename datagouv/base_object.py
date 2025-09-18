import logging
import re
from typing import Iterator

import httpx

from .client import Client
from .retry import simple_connection_retry


def assert_auth(client: Client) -> None:
    if not client._authenticated:
        raise PermissionError(
            "This method requires authentication, please specify your API key in the Client"
        )


class BaseObject:
    uri: str
    _attributes: list[str] = []

    def __init__(self, id: str, _client: Client = Client()):
        self.id = id
        self._client = _client
        self._base_metrics_url = (
            f"https://metric-api.data.gouv.fr/api/{self.__class__.__name__.lower()}s/"
            f"data/?{self.__class__.__name__.lower()}_id__exact={id}"
            if self._client.environment == "www"
            else None
        )

    def __repr__(self) -> str:
        return str(self.__dict__)

    @simple_connection_retry
    def refresh(self, _from_response: dict | None = None) -> dict:
        if _from_response:
            metadata = _from_response
        else:
            r = self._client.session.get(self.uri)
            r.raise_for_status()
            metadata = r.json()
        for a in self._attributes:
            setattr(self, a, metadata.get(a))
        return metadata

    @simple_connection_retry
    def update(self, payload: dict) -> httpx.Response:
        assert_auth(self._client)
        logging.info(f"🔁 Putting {self.uri} with {payload}")
        r = self._client.session.put(self.uri, json=payload)
        r.raise_for_status()
        self.refresh(_from_response=r.json())
        return r

    @simple_connection_retry
    def delete(self) -> httpx.Response:
        assert_auth(self._client)
        logging.info(f"🚮 Deleting {self.uri}")
        r = self._client.session.delete(self.uri)
        r.raise_for_status()
        return r

    @simple_connection_retry
    def update_extras(self, payload: dict) -> httpx.Response:
        assert_auth(self._client)
        logging.info(f"🔁 Putting {self.uri} with extras {payload}")
        r = self._client.session.put(self.uri.replace("api/1", "api/2") + "extras/", json=payload)
        r.raise_for_status()
        self.refresh()
        return r

    @simple_connection_retry
    def delete_extras(self, payload: dict) -> httpx.Response:
        assert_auth(self._client)
        logging.info(f"🚮 Deleting extras {payload} for {self.uri}")
        r = self._client.session.delete(
            self.uri.replace("api/1", "api/2") + "extras/",
            json=payload,  # pyright: ignore[reportCallIssue] udata handles body on DELETE
        )
        r.raise_for_status()
        self.refresh()
        return r

    @simple_connection_retry
    def get_monthly_traffic_metrics(
        self, start_month: str | None = None, end_month: str | None = None
    ) -> Iterator[dict]:
        if self._base_metrics_url is None:
            raise ValueError("Metrics not available for this object on this env.")
        url = self._base_metrics_url
        if start_month is not None:
            if not re.match(r"^\d{4}-\d{2}$", start_month):
                raise ValueError("`start_month` must look like YYYY-MM")
            url += f"&metric_month__greater={start_month}"
        if end_month is not None:
            if not re.match(r"^\d{4}-\d{2}$", end_month):
                raise ValueError("`end_month` must look like YYYY-MM")
            url += f"&metric_month__less={end_month}"
        return Client().get_all_from_api_query(
            url,
            next_page="links.next",
            _ignore_base_url=True,
        )


class Creator:
    def __init__(self, _client):
        self._client = _client
