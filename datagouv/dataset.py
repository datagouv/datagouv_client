import logging
from pathlib import Path

from .base_object import BaseObject, Creator, assert_auth
from .client import Client
from .resource import Resource, ResourceCreator
from .retry import simple_connection_retry


class Dataset(BaseObject, ResourceCreator):
    _attributes = [
        "archived",
        "badges",
        "contact_points",
        "created_at",
        "deleted",
        "description",
        "harvest",
        "internal",
        "last_modified",
        "last_update",
        "metrics",
        "owner",
        "tags",
        "title",
        "extras",
    ]

    def __init__(
        self,
        id: str,
        fetch: bool = True,
        _client: Client = Client(),
        _from_response: dict | None = None,
    ):
        BaseObject.__init__(self, id, _client)
        self.uri = f"{_client.base_url}/api/1/datasets/{id}/"
        self.front_url = self.uri.replace("/api/1", "")
        if fetch or _from_response:
            self.refresh(_from_response=_from_response)

    def __call__(self, *args, **kwargs):
        return Dataset(*args, **kwargs)

    def refresh(self, _from_response: dict | None = None):
        from .organization import Organization

        BaseObject.refresh(self, _from_response)
        if _from_response:
            resources = _from_response["resources"]
            organization = _from_response["organization"]
        else:
            metadata = self._client.session.get(self.uri).json()
            resources = metadata["resources"]
            organization = metadata["organization"]
        self.resources = (
            [
                Resource(id=r["id"], dataset_id=self.id, _client=self._client, _from_response=r)
                for r in resources
            ]
            if isinstance(resources, list)
            # when coming from api/2 the resources have to be retrieved
            else [
                Resource(id=r["id"], dataset_id=self.id, _client=self._client, _from_response=r)
                for r in self._client.get_all_from_api_query(
                    resources["href"],
                    _ignore_base_url=True,
                )
            ]
        )
        self.organization = (
            Organization(organization["id"], _from_response=organization)
            if organization is not None
            else None
        )

    def download_resources(
        self, folder: Path | str | None = None, resources_types: list[str] = ["main"]
    ):
        for res in self.resources:
            if res.type in resources_types:
                if folder is not None:
                    folder_path = Path(folder) if isinstance(folder, str) else folder
                    # Ensure the folder exists
                    folder_path.mkdir(parents=True, exist_ok=True)
                    path = folder_path / f"{res.id}.{res.format}"
                else:
                    path = None
                logging.info(f"Downloading {res.url}")
                res.download(path=path)


class DatasetCreator(Creator):
    @simple_connection_retry
    def create(self, payload: dict) -> Dataset:
        assert_auth(self._client)
        logging.info(f"Creating dataset '{payload['title']}'")
        r = self._client.session.post(f"{self._client.base_url}/api/1/datasets/", json=payload)
        r.raise_for_status()
        metadata = r.json()
        return Dataset(metadata["id"], _client=self._client, _from_response=metadata)
