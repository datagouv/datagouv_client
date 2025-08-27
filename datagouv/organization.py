import logging
from typing import Iterator

from .base_object import BaseObject, Creator, assert_auth
from .client import Client
from .dataset import Dataset, DatasetCreator
from .retry import simple_connection_retry


class Organization(BaseObject):
    _attributes = [
        "badges",
        "business_number_id",
        "created_at",
        "deleted",
        "description",
        "last_modified",
        "members",
        "metrics",
        "name",
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
        self.uri = f"{_client.base_url}/api/1/organizations/{id}/"
        self.front_url = self.uri.replace("/api/1", "")
        if fetch or _from_response:
            self.refresh(_from_response=_from_response)

    def datasets(self) -> Iterator[Dataset]:
        for item in self._client.get_all_from_api_query(f"api/1/organizations/{self.id}/datasets/"):
            yield Dataset(item["id"], _client=self._client, _from_response=item)

    def create_dataset(self, payload: dict) -> Dataset:
        # we don't simply heritate from DatasetCreator to have a different method name
        for key in ["organization", "owner"]:
            if payload.get(key):
                raise ValueError(
                    f"It is not possible to specify the {key} when creating a dataset "
                    "from an organization, it will be attached to it."
                )
        return DatasetCreator(_client=self._client).create(
            payload=payload | {"organization": self.id}
        )


class OrganizationCreator(Creator):
    @simple_connection_retry
    def create(self, payload: dict) -> Organization:
        assert_auth(self._client)
        logging.info(f"Creating organization '{payload['name']}'")
        r = self._client.session.post(f"{self._client.base_url}/api/1/organizations/", json=payload)
        r.raise_for_status()
        metadata = r.json()
        return Organization(metadata["id"], _client=self._client, _from_response=metadata)
