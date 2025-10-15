import logging
from typing import Iterator

import httpx

from .base_object import BaseObject, Creator, assert_auth
from .client import Client
from .dataset import Dataset
from .retry import simple_connection_retry


class Topic(BaseObject):
    _elements: list | None = None
    _datasets: list | None = None

    _attributes = [
        "created_at",
        "description",
        "featured",
        "last_modified",
        "name",
        "owner",
        "private",
        "slug",
        "spatial",
        "tags",
        "extras",
    ]

    def __init__(
        self,
        id: str | None = None,
        fetch: bool = True,
        _client: Client = Client(),
        _from_response: dict | None = None,
    ):
        BaseObject.__init__(self, id, _client)
        self.uri = f"{_client.base_url}/api/2/topics/{id}/"
        if fetch or _from_response:
            self.refresh(_from_response=_from_response)

    def __call__(self, *args, **kwargs):
        return Topic(*args, **kwargs)

    def refresh(self, _from_response: dict | None = None, include_elements: bool = False) -> dict:
        from .organization import Organization

        metadata = super().refresh(_from_response)
        organization = metadata["organization"]
        self.organization = (
            Organization(organization["id"], _from_response=organization)
            if organization is not None
            else None
        )

        if include_elements:
            # invalidate caches so that the next call will fetch fresh data
            self._elements = None
            self._datasets = None

        return metadata

    @property
    def elements(self) -> Iterator[dict]:
        """Lazy fetch elements in raw form"""
        if self._elements is None:
            self._elements = list(
                self._client.get_all_from_api_query(f"{self.uri}elements/", _ignore_base_url=True)
            )
        yield from self._elements

    @property
    def datasets(self) -> Iterator[Dataset]:
        """Lazy fetch topic.Datasets"""
        if self._datasets is None:
            self._datasets = []
            for element in self.elements:
                if (element["element"] or {}).get("class") == "Dataset":
                    self._datasets.append(Dataset(element["element"]["id"]))
        yield from self._datasets

    def get_monthly_traffic_metrics(self, *args, **kwargs) -> Iterator[dict]:
        raise NotImplementedError()

    def delete_extras(self, *args, **kwargs) -> httpx.Response:
        raise NotImplementedError()

    def update_extras(self, *args, **kwargs) -> httpx.Response:
        raise NotImplementedError()


class TopicCreator(Creator):
    @simple_connection_retry
    def create(self, payload: dict) -> Topic:
        assert_auth(self._client)
        logging.info(f"Creating topic '{payload['name']}'")
        r = self._client.session.post(f"{self._client.base_url}/api/2/topics/", json=payload)
        r.raise_for_status()
        metadata = r.json()
        return Topic(metadata["id"], _client=self._client, _from_response=metadata)
