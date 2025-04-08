import logging

from .base_object import BaseObject, Creator, assert_auth
from .client import Client
from .retry import simple_connection_retry


class Resource(BaseObject):
    _attributes = [
        "created_at",
        "description",
        "filetype",
        "filesize",
        "internal",
        "last_modified",
        "schema",
        "title",
        "type",
        "url",
        "extras",
    ]

    def __init__(
        self,
        id: str,
        dataset_id: str | None = None,
        is_communautary: bool = False,
        _from_response: dict | None = None,
        _client: Client = Client(),
    ):
        super().__init__(id, _client)
        if not dataset_id:
            response = self.get_api2_metadata()
            # we prevent another api call because we have the metadata here
            dataset_id, _from_response = response["dataset_id"], response["resource"]
        self.dataset_id = dataset_id
        self.uri = (
            f"{_client.base_url}/api/1/datasets/{self.dataset_id}/resources/{self.id}/"
            if not is_communautary and self.dataset_id is not None
            else f"{_client.base_url}/api/1/datasets/community_resources/{self.id}"
        )
        self.front_url = self.uri.replace("api/1", "fr").replace(
            "/resources", "/#/resources"
        )
        self.refresh(_from_response=_from_response)

    def dataset(self):
        # we cannot instanciate the dataset in the init, because it would infinitely loop
        # between the dataset and its resources (each one creating the other)
        # it makes more sense that a dataset has its resources instantiated at init
        # so resources must have dataset as a separate method
        from .dataset import Dataset

        return Dataset(self.dataset_id, _client=self._client)

    def get_api2_metadata(self):
        r = self._client.session.get(
            f"{self._client.base_url}/api/2/datasets/resources/{self.id}/"
        )
        r.raise_for_status()
        return r.json()

    @simple_connection_retry
    def check_if_more_recent_update(
        self,
        dataset_id: str,
    ) -> bool:
        """
        Checks whether any resource of the specified dataset has been updated more recently
        than the specified resource
        """
        resources = self._client.session.get(
            f"{self._client.base_url}/api/1/datasets/{dataset_id}/",
            headers={"X-fields": "resources{internal{last_modified_internal}}"},
        ).json()["resources"]
        latest_update = self._client.session.get(
            f"{self._client.base_url}/api/2/datasets/resources/{self.id}/",
            headers={"X-fields": "resource{internal{last_modified_internal}}"},
        ).json()["resource"]["internal"]["last_modified_internal"]
        return any(
            r["internal"]["last_modified_internal"] > latest_update for r in resources
        )


class ResourceCreator(Creator):
    @simple_connection_retry
    def create_remote(
        self,
        payload: dict,
        dataset_id: str | None = None,
        is_communautary: bool = False,
    ) -> Resource:
        if dataset_id and self.__class__.__name__ == "Dataset":
            raise ValueError(
                "When creating a resource from a dataset, you should't specify a dataset_id"
            )
        assert_auth(self._client)
        if not dataset_id:
            if self.__class__.__name__ == "Dataset":
                dataset_id = self.id
            else:
                raise ValueError("A dataset_id must be specified")
        if is_communautary:
            url = f"{self._client.base_url}/api/1/datasets/community_resources/"
            payload["dataset"] = {"class": "Dataset", "id": dataset_id}
        else:
            url = f"{self._client.base_url}/api/1/datasets/{dataset_id}/resources/"
        logging.info(f"Creating '{payload['title']}' at {url}")
        if "filetype" not in payload:
            payload.update({"filetype": "remote"})
        if "type" not in payload:
            payload.update({"type": "main"})
        r = self._client.session.post(url, json=payload)
        r.raise_for_status()
        metadata = r.json()
        return Resource(metadata["id"], _client=self._client, _from_response=metadata)

    @simple_connection_retry
    def create_static(
        self,
        file_to_upload: str,  # the path of the file
        payload: dict,
        dataset_id: str | None = None,
        is_communautary: bool = False,
    ) -> Resource:
        if dataset_id and self.__class__.__name__ == "Dataset":
            raise ValueError(
                "When creating a resource from a dataset, you should't specify a dataset_id"
            )
        assert_auth(self._client)
        if not dataset_id:
            if self.__class__.__name__ == "Dataset":
                dataset_id = self.id
            else:
                raise ValueError("A dataset_id must be specified")
        url = f"{self._client.base_url}/api/1/datasets/{dataset_id}/upload/"
        if is_communautary:
            url += "community/"
        r = self._client.session.post(url, files={"file": open(file_to_upload, "rb")})
        r.raise_for_status()
        metadata = r.json()
        resource_id = metadata["id"]
        logging.info(f"Resource was given this id: {resource_id}")
        r = Resource(
            id=resource_id,
            dataset_id=dataset_id,
            is_communautary=is_communautary,
            _client=self._client,
            _from_response=metadata,
        )
        if "type" not in payload:
            payload.update({"type": "main"})
        r.update_metadata(payload=payload)
        return r
