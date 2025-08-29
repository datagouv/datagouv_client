import logging

import httpx

from .client import Client
from .retry import simple_connection_retry


def assert_auth(client: Client) -> None:
    if not client._authenticated:
        raise PermissionError(
            "This method requires authentication, please specify your API key in the Client"
        )


class BaseObject:
    def __init__(self, id: str | None = None, _client: Client = Client()):
        self.id = id
        self._client = _client

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
            self.uri.replace("api/1", "api/2") + "extras/", json=payload
        )
        r.raise_for_status()
        self.refresh()
        return r


class Creator:
    def __init__(self, _client):
        self._client = _client
