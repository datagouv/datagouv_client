from typing import TYPE_CHECKING, Iterator

import httpx

if TYPE_CHECKING:
    from datagouv import Dataset, Organization, Resource, Topic


class Client:
    _envs = ["www", "demo", "dev"]

    def __init__(self, environment: str = "www", api_key: str | None = None):
        if environment not in self._envs:
            raise ValueError(f"`environment` must be in {self._envs}")
        self.base_url = f"https://{environment}.data.gouv.fr"
        self.session = httpx.Client()
        self.environment = environment
        self._authenticated = False
        if api_key:
            self._authenticated = True
            self.session.headers.update({"X-API-KEY": api_key})

    def resource(self, id: str | None = None, **kwargs):
        from .resource import Resource, ResourceCreator

        if id:
            return Resource(id, _client=self, **kwargs)
        return ResourceCreator(_client=self)

    def dataset(self, id: str | None = None, **kwargs):
        from .dataset import Dataset, DatasetCreator

        if id:
            return Dataset(id, _client=self, **kwargs)
        return DatasetCreator(_client=self)

    def topic(self, id: str | None = None, **kwargs):
        from .topic import Topic, TopicCreator

        if id:
            return Topic(id, _client=self, **kwargs)
        return TopicCreator(_client=self)

    def organization(self, id: str | None = None, **kwargs):
        from .organization import Organization, OrganizationCreator

        if id:
            return Organization(id, _client=self, **kwargs)
        return OrganizationCreator(_client=self)

    def get_all_from_api_query(
        self,
        base_query: str,
        next_page: str = "next_page",
        mask: str | None = None,
        _ignore_base_url: bool = False,
        cast_as: "Dataset|Organization|Resource|Topic|None" = None,
    ) -> Iterator["Dataset|Organization|Resource|Topic|dict"]:
        """⚠️ only for paginated endpoints"""

        def get_link_next_page(elem: dict, separated_keys: str) -> str | None:
            result = elem
            for k in separated_keys.split("."):
                if k not in result or result[k] is None:
                    return None
                result = result[k]
            return result if isinstance(result, str) else None

        def cast_elem(
            elem: dict,
            client: Client,
            cast_as: "Dataset|Organization|Resource|Topic|None",
        ) -> "Dataset|Organization|Resource|Topic|dict":
            return (
                elem
                if cast_as is None
                else cast_as(
                    elem["id"],
                    _client=client,
                    _from_response=elem,
                )
            )

        headers = {}
        if mask is not None:
            headers["X-fields"] = mask + f",{next_page}"
        r = self.session.get(
            base_query if _ignore_base_url else f"{self.base_url}/{base_query}",
            headers=headers,
        )
        r.raise_for_status()
        for elem in r.json()["data"]:
            yield cast_elem(elem, self, cast_as)
        next_url = get_link_next_page(r.json(), next_page)
        while next_url:
            r = self.session.get(next_url, headers=headers)
            r.raise_for_status()
            for data in r.json()["data"]:
                yield cast_elem(data, self, cast_as)
            next_url = get_link_next_page(r.json(), next_page)
