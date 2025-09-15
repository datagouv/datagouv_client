from .base_object import BaseObject
from .client import Client
from .dataset import Dataset


class Topic(BaseObject):
    _elements: list | None = None
    _datasets: list | None = None

    _attributes = [
        "created_at",
        "description",
        "featured",
        "last_modified",
        "name",
        "owner",
        "private",
        "slug",
        "spatial",
        "tags",
        "uri",
        "extras",
    ]

    def __init__(
        self,
        id: str | None = None,
        _client: Client = Client(),
        _from_response: dict | None = None,
    ):
        BaseObject.__init__(self, id, _client)
        self.uri = f"{_client.base_url}/api/2/topics/{id}/"
        self.refresh(_from_response=_from_response)

    def refresh(self, _from_response: dict | None = None, include_elements: bool = False) -> dict:
        from .organization import Organization

        metadata = super().refresh(_from_response)
        organization = metadata["organization"]
        self.organization = (
            Organization(organization["id"], _from_response=organization)
            if organization is not None
            else None
        )

        if include_elements:
            # invalidate caches so that the next call will fetch fresh data
            self._elements = None
            self._datasets = None

        return metadata

    @property
    def elements(self) -> list[dict]:
        """Lazy fetch elements in raw form"""
        if self._elements is None:
            self._elements = list(
                self._client.get_all_from_api_query(f"{self.uri}elements/")
            )
        return self._elements

    @property
    def datasets(self) -> list[Dataset]:
        """Lazy fetch topic.Datasets"""
        if self._datasets is None:
            self._datasets = []
            for element in self.elements:
                if (element["element"] or {}).get("class") == "Dataset":
                    self._datasets.append(Dataset(element["element"]["id"]))
        return self._datasets
