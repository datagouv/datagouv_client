import logging
from io import BytesIO
from pathlib import Path

import httpx

from .base_object import BaseObject, Creator, assert_auth
from .client import Client
from .retry import simple_connection_retry


class Resource(BaseObject):
    _dataset = None
    _attributes = [
        "checksum",
        "created_at",
        "description",
        "filesize",
        "filetype",
        "format",
        "harvest",
        "internal",
        "last_modified",
        "mime",
        "preview_url",
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
        fetch: bool = True,
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
            else f"{_client.base_url}/api/1/datasets/community_resources/{self.id}/"
        )
        self.front_url = self.uri.replace("/api/1", "").replace("/resources", "/#/resources")
        if fetch or _from_response:
            self.refresh(_from_response=_from_response)

    def __call__(self, *args, **kwargs):
        return Resource(*args, **kwargs)

    def refresh(self, _from_response: dict | None = None):
        metadata = super().refresh(_from_response)
        self._dataset = None
        return metadata

    def update(self, payload: dict, file_to_upload: str | None = None, timeout: int = 30):
        assert_auth(self._client)
        if file_to_upload:
            if self.filetype != "file":
                raise ValueError(
                    "This resource is not static, you can't upload a file. "
                    "To modify the URL it points to, please use the `url` field in the payload."
                )
            if self._client.verbose:
                logging.info(f"⬆️ Posting file {file_to_upload} into {self.uri}")
            try:
                r = self._client.session.post(
                    f"{self.uri}upload/",
                    files={"file": open(file_to_upload, "rb")},
                    timeout=timeout,
                )
            except httpx.TimeoutException as e:
                raise TimeoutError(
                    "The upload reached the timeout, consider setting it higher like:"
                    f" update(..., timeout={timeout * 2})"
                ) from e
            try:
                r.raise_for_status()
            except Exception as e:
                raise Exception(r.text) from e
        return super().update(payload)

    @property
    def dataset(self):
        # we cannot instanciate the dataset in the init, because it would infinitely loop
        # between the dataset and its resources (each one creating the other)
        # it makes more sense that a dataset has its resources instantiated at init
        # so resources must have dataset as a separate method
        from .dataset import Dataset

        if self._dataset is None:
            dataset = Dataset(self.dataset_id, _client=self._client)
            self._dataset = dataset
        return self._dataset

    def _iter_download(self, chunk_size: int = 8192, **kwargs):
        with httpx.stream("GET", self.url, **kwargs) as r:
            try:
                r.raise_for_status()
            except Exception as e:
                raise Exception(r.text) from e
            for chunk in r.iter_bytes(chunk_size=chunk_size):
                yield chunk

    def download_buffer(
        self,
        chunk_size: int = 8192,
        max_mib: float | None = 95,
        **kwargs,
    ) -> BytesIO:
        """Download the file into memory and return it as a BytesIO buffer.

        The response is streamed in chunks and accumulated in memory.
        Use `chunk_size` to control read granularity and `max_mib` to
        enforce an upper size limit to prevent excessive memory usage.

        Note:
            100 MB ≈ 95 MiB.
        """

        max_bytes = None if max_mib is None else int(max_mib * 1024**2)

        buf = BytesIO()
        total = 0

        for chunk in self._iter_download(chunk_size=chunk_size, **kwargs):
            buf.write(chunk)
            total += len(chunk)

            if max_bytes is not None and total > max_bytes:
                raise ValueError(
                    f"Response too large (> {max_mib} MiB). Consider increasing `max_mib` value."
                )

        buf.seek(0)
        return buf

    def download(self, path: Path | str | None = None, chunk_size: int = 8192, **kwargs):
        if path is None:
            path = Path(f"{self.id}.{self.format}")
        if isinstance(path, str):
            path = Path(path)
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        chunks = self._iter_download(chunk_size)
        with open(path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

    def get_api2_metadata(self) -> dict:
        r = self._client.session.get(f"{self._client.base_url}/api/2/datasets/resources/{self.id}/")
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(r.text) from e
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
        return any(r["internal"]["last_modified_internal"] > latest_update for r in resources)


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
        if self._client.verbose:
            logging.info(f"🆕 Creating '{payload['title']}' for {url}")
        if "filetype" not in payload:
            payload.update({"filetype": "remote"})
        if "type" not in payload:
            payload.update({"type": "main"})
        r = self._client.session.post(url, json=payload)
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(r.text) from e
        metadata = r.json()
        return Resource(
            metadata["id"], dataset_id=dataset_id, _client=self._client, _from_response=metadata
        )

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
        if self._client.verbose:
            logging.info(f"🆕 Creating '{payload['title']}' for {file_to_upload}")
        r = self._client.session.post(url, files={"file": open(file_to_upload, "rb")})
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(r.text) from e
        metadata = r.json()
        resource_id = metadata["id"]
        r = Resource(
            id=resource_id,
            dataset_id=dataset_id,
            is_communautary=is_communautary,
            _client=self._client,
            _from_response=metadata,
        )
        if "type" not in payload:
            payload.update({"type": "main"})
        r.update(payload=payload)
        return r
