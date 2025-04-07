import logging

from .client import Client
from .base_object import BaseObject, Creator, assert_auth
from .resource import Resource, ResourceCreator
from .retry import simple_connection_retry


class Dataset(BaseObject, ResourceCreator):
    _attributes = [
        "created_at",
        "description",
        "last_modified",
        "title",
        "extras",
    ]

    def __init__(
        self,
        id: str | None = None,
        _client: Client = Client(),
        _from_response: dict | None = None,
    ):
        BaseObject.__init__(self, id, _client)
        self.uri = f"{_client.base_url}/api/1/datasets/{id}/"
        self.front_url = self.uri.replace("api/1", "fr")
        self.refresh(_from_response=_from_response)

    def refresh(self, _from_response: dict | None = None):
        BaseObject.refresh(self, _from_response)
        if _from_response:
            resources = _from_response["resources"]
        else:
            resources = self._client.session.get(self.uri).json()["resources"]
        self.resources = [
            Resource(
                id=r["id"], dataset_id=self.id, _client=self._client, _from_response=r
            )
            for r in resources
        ]


class DatasetCreator(Creator):
    @simple_connection_retry
    def create(self, payload: dict) -> Dataset:
        assert_auth(self._client)
        logging.info(f"Creating dataset '{payload['title']}'")
        r = self._client.session.post(
            f"{self._client.base_url}/api/1/datasets/", json=payload
        )
        r.raise_for_status()
        metadata = r.json()
        return Dataset(metadata["id"], _client=self._client, _from_response=metadata)
