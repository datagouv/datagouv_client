import logging
import re
from typing import Iterator, Optional

import niquests

from datagouv.api.client import Client
from datagouv.api.dataset import Dataset
from datagouv.utils.base_object import BaseObject, Creator, assert_auth
from datagouv.utils.retry import simple_connection_retry


class API(BaseObject):
    _attributes = [
        "access_audiences",
        "access_type",
        "badges",
        "base_api_url",
        "business_documentation_url",
        "created_at",
        "deleted_at",
        "description",
        "extras",
        "last_modified",
        "machine_documentation_url",
        "metrics",
        "organization",
        "rate_limiting",
        "tags",
        "title",
        "url",
    ]

    def __init__(
        self,
        id: str,
        fetch: bool = True,
        _client: Client = Client(),
        _from_response: dict | None = None,
    ):
        BaseObject.__init__(self, id, _client)
        self.uri = f"{_client.base_url}/api/1/dataservices/{id}/"
        self.front_url = self.uri.replace("/api/1", "")
        if fetch or _from_response:
            self.refresh(_from_response=_from_response)

    def __call__(self, *args, **kwargs):
        return API(*args, **kwargs)

    # TODO: to avoid code duplication, _update_method could be a class-level attribute
    def update(self, payload: dict) -> niquests.Response:
        assert_auth(self._client)
        if not isinstance(payload, dict):
            raise TypeError(f"payload should be a dictionary and not {type(payload)}")

        if self._client.verbose:
            logging.info(f"🔁 Putting {self.uri} with {payload}")
        r = self._client.session.patch(self.uri, json=payload)
        r.raise_for_status()
        self.refresh(_from_response=r.json())
        return r

    @property
    def organization_id(self) -> Optional[str]:
        if self.organization:  # type: ignore
            return self.organization["id"]  # type: ignore

    @property
    def associated_datasets(self) -> Iterator[Dataset]:
        if not re.fullmatch(r"[0-9a-f]{24}", self.id):
            raise Exception(
                f"Current API's ID is a slug : {self.id}. Please recreate the object with its ID."
            )
        url = f"api/1/datasets/?dataservice={self.id}"
        response = self._client.get_all_from_api_query(base_query=url, cast_as=Dataset)
        return response  # type: ignore - we cast as Dataset in the function


class APICreator(Creator):
    @simple_connection_retry
    def create(self, payload: dict) -> API:
        assert_auth(self._client)
        if self._client.verbose:
            logging.info(f"Creating third-party API '{payload['title']}'")
        r = self._client.session.post(f"{self._client.base_url}/api/1/dataservices/", json=payload)
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(r.text) from e
        metadata = r.json()
        return API(metadata["id"], _client=self._client, _from_response=metadata)
