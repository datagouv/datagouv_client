from typing import Iterator

import requests

from .retry import simple_connection_retry


class Client:
    _envs = ["www", "demo", "dev"]

    def __init__(self, environment: str = "www", api_key: str | None = None):
        if environment not in self._envs:
            raise ValueError(f"`environment` must be in {self._envs}")
        self.base_url = f"https://{environment}.data.gouv.fr"
        self.session = requests.Session()
        self._authenticated = False
        if api_key:
            self._authenticated = True
            self.session.headers.update({"X-API-KEY": api_key})

    def resource(self, id: str | None = None, **kwargs):
        from .dataset import Resource, ResourceCreator

        if id:
            return Resource(id, _client=self, **kwargs)
        return ResourceCreator(_client=self)

    def dataset(self, id: str | None = None):
        from .dataset import Dataset, DatasetCreator

        if id:
            return Dataset(id, _client=self)
        return DatasetCreator(_client=self)

    @simple_connection_retry
    def get_dataset_id(self, resource_id: str) -> str | None:
        # communautary resources return None
        url = f"{self.base_url}/api/2/datasets/resources/{resource_id}/"
        r = requests.get(url)
        r.raise_for_status()
        return r.json()["dataset_id"]

    def get_all_from_api_query(
        self,
        base_query: str,
        next_page: str = "next_page",
        ignore_errors: bool = False,
        mask: str | None = None,
    ) -> Iterator[dict]:
        """/!\ only for paginated endpoints"""

        def get_link_next_page(elem: dict, separated_keys: str):
            result = elem
            for k in separated_keys.split("."):
                result = result[k]
            return result

        headers = {}
        if mask is not None:
            headers["X-fields"] = mask + f",{next_page}"
        r = self.session.get(base_query, headers=headers)
        if not ignore_errors:
            r.raise_for_status()
        for elem in r.json()["data"]:
            yield elem
        while get_link_next_page(r.json(), next_page):
            r = self.session.get(
                get_link_next_page(r.json(), next_page), headers=headers
            )
            if not ignore_errors:
                r.raise_for_status()
            for data in r.json()["data"]:
                yield data
