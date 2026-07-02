from importlib.metadata import version
from typing import TYPE_CHECKING, Iterator

import niquests

if TYPE_CHECKING:
    from datagouv import API, Dataset, Organization, Resource, Topic

PYTHON_USER_AGENT = {"User-Agent": f"datagouv-python/{version('datagouv_client')}"}


class Client:
    _envs = {
        "www": "www",
        "prod": "www",
        "demo": "demo",
        "dev": "dev",
    }

    def __init__(
        self,
        environment: str = "www",
        api_key: str | None = None,
        *,
        verbose: bool = True,
        **kwargs,
    ):
        self._env_sanity(environment)
        self.session = niquests.Session(**({"timeout": 15, "headers": PYTHON_USER_AGENT} | kwargs))
        self.environment = self._envs[environment]
        self.base_url = f"https://{self.environment}.data.gouv.fr"
        self.verbose = verbose
        self._authenticated = False
        if api_key:
            self._authenticated = True
            self.session.headers.update({"X-API-KEY": api_key})

    @classmethod
    def _env_sanity(cls, environment: str) -> None:
        if environment not in cls._envs:
            raise ValueError(f"`environment` must be in {list(cls._envs)}")

    def resource(self, id: str, **kwargs) -> "Resource":
        from datagouv.api.resource import Resource

        return Resource(id, _client=self, **kwargs)

    def create_remote_resource(
        self, payload: dict, dataset_id: str, is_communautary: bool = False
    ) -> "Resource":
        """Create a resource that references a data stored somewhere else on the internet."""
        from datagouv.api.resource import ResourceCreator

        return ResourceCreator(_client=self).create_remote(
            payload, dataset_id, is_communautary=is_communautary
        )

    def create_static_resource(
        self, file_to_upload: str, payload: dict, dataset_id: str, is_communautary: bool = False
    ) -> "Resource":
        """Create a resource by uploading a file on datagouv storage."""
        from datagouv.api.resource import ResourceCreator

        return ResourceCreator(_client=self).create_static(
            file_to_upload, payload, dataset_id, is_communautary=is_communautary
        )

    def dataset(self, id: str, **kwargs) -> "Dataset":
        from datagouv.api.dataset import Dataset

        return Dataset(id, _client=self, **kwargs)

    def api(self, id: str, **kwargs) -> "API":
        from datagouv.api.api import API

        return API(id, _client=self, **kwargs)

    def create_dataset(self, payload: dict) -> "Dataset":
        from datagouv.api.dataset import DatasetCreator

        return DatasetCreator(_client=self).create(payload=payload)

    def create_API(self, payload: dict) -> "API":
        from datagouv.api.api import APICreator

        return APICreator(_client=self).create(payload=payload)

    def topic(self, id: str, **kwargs) -> "Topic":
        from datagouv.api.topic import Topic

        return Topic(id, _client=self, **kwargs)

    def create_topic(self, payload: dict) -> "Topic":
        from datagouv.api.topic import TopicCreator

        return TopicCreator(_client=self).create(payload=payload)

    def organization(self, id: str, **kwargs) -> "Organization":
        from datagouv.api.organization import Organization

        return Organization(id, _client=self, **kwargs)

    def create_organization(self, payload: dict) -> "Organization":
        from datagouv.api.organization import OrganizationCreator

        return OrganizationCreator(_client=self).create(payload=payload)

    def get_all_from_api_query(
        self,
        base_query: str,
        next_page: str = "next_page",
        mask: str | None = None,
        _ignore_base_url: bool = False,
        cast_as: type["Dataset | Organization | Resource | Topic"] | None = None,
    ) -> Iterator["Dataset | Organization | Resource | Topic | dict"]:
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
            cast_as: type["Dataset | Organization | Resource | Topic"] | None,
        ) -> "Dataset | Organization | Resource | Topic | dict":
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
        try:
            r.raise_for_status()
        except Exception as e:
            raise Exception(r.text) from e
        for elem in r.json()["data"]:
            yield cast_elem(elem, self, cast_as)
        next_url = get_link_next_page(r.json(), next_page)
        while next_url:
            r = self.session.get(next_url, headers=headers)
            try:
                r.raise_for_status()
            except Exception as e:
                raise Exception(r.text) from e
            for data in r.json()["data"]:
                yield cast_elem(data, self, cast_as)
            next_url = get_link_next_page(r.json(), next_page)
