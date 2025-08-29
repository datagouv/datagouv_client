from typing import Iterator

import httpx


class Client:
    _envs = ["www", "demo", "dev"]

    def __init__(self, environment: str = "www", api_key: str | None = None):
        if environment not in self._envs:
            raise ValueError(f"`environment` must be in {self._envs}")
        self.base_url = f"https://{environment}.data.gouv.fr"
        self.session = httpx.Client()
        self._authenticated = False
        if api_key:
            self._authenticated = True
            self.session.headers.update({"X-API-KEY": api_key})

    def resource(self, id: str | None = None, **kwargs):
        from .resource import Resource, ResourceCreator

        if id:
            return Resource(id, _client=self, **kwargs)
        return ResourceCreator(_client=self)

    def dataset(self, id: str | None = None, fetch: bool = True):
        from .dataset import Dataset, DatasetCreator

        if id:
            return Dataset(id, _client=self, fetch=fetch)
        return DatasetCreator(_client=self)

    def organization(self, id: str | None = None, fetch: bool = True):
        from .organization import Organization, OrganizationCreator

        if id:
            return Organization(id, _client=self, fetch=fetch)
        return OrganizationCreator(_client=self)

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
        r = self.session.get(f"{self.base_url}/{base_query}", headers=headers)
        if not ignore_errors:
            r.raise_for_status()
        for elem in r.json()["data"]:
            yield elem
        while get_link_next_page(r.json(), next_page):
            r = self.session.get(get_link_next_page(r.json(), next_page), headers=headers)
            if not ignore_errors:
                r.raise_for_status()
            for data in r.json()["data"]:
                yield data
