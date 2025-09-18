from unittest.mock import patch

import pytest
from conftest import OWNER_ID, TOPIC_ID, elements_metadata, topic_metadata

from datagouv.base_object import BaseObject
from datagouv.client import Client
from datagouv.dataset import Dataset
from datagouv.organization import Organization
from datagouv.topic import Topic, TopicCreator


def test_dataset_instance(topic_api_call):
    assert isinstance(Client().topic(TOPIC_ID), Topic)
    assert isinstance(Client().topic(), TopicCreator)


def test_topic_attributes_and_methods(topic_api_call):
    client = Client()
    topic = client.topic(TOPIC_ID)
    with patch("httpx.Client.get") as mock_func:
        topic_from_response = Topic(TOPIC_ID, _from_response=topic_metadata)
        # when instanciating from a response, we don't call the API another time
        mock_func.assert_not_called()
    for attribute in (
        [
            "id",
            "uri",
            "organization",
        ]
        + Topic._attributes
        + [method for method in dir(BaseObject) if not method.startswith("__")]
    ):
        assert attribute in dir(topic)
        assert attribute in dir(topic_from_response)
    assert isinstance(topic.organization, Organization)


def test_elements(topic_api_call, elements_api_call):
    topic = Topic(TOPIC_ID)
    elements = topic.elements
    assert len(list(elements)) == len(elements_metadata["data"])


def test_datasets(topic_api_call, elements_api_call, dataset_catchall_api_call):
    topic = Topic(TOPIC_ID)
    datasets = topic.datasets
    assert len(list(datasets)) == len(
        [
            e
            for e in elements_metadata["data"]
            if e["element"] and e["element"]["class"] == "Dataset"
        ]
    )
    assert all(isinstance(d, Dataset) for d in datasets)


def test_topic_has_owner():
    owner = {"id": OWNER_ID}
    topic_with_owner = Topic(
        TOPIC_ID,
        _from_response=topic_metadata | {"organization": None} | {"owner": owner},
    )
    assert topic_with_owner.organization is None
    assert topic_with_owner.owner == owner


def test_topic_no_fetch():
    with patch("httpx.Client.get") as mock_func:
        d = Topic(TOPIC_ID, fetch=False)
        mock_func.assert_not_called()
    print([getattr(d, a, None) for a in Topic._attributes])
    assert all(getattr(d, a, None) is None for a in Topic._attributes)
    assert d.uri


def test_authentification_assertion():
    client = Client()
    with pytest.raises(PermissionError):
        client.topic().create({"name": "Test Topic"})


def test_topic_create(httpx_mock):
    # Mock the API response for topic creation
    httpx_mock.add_response(
        method="POST",
        url="https://www.data.gouv.fr/api/2/topics/",
        json=topic_metadata,
        status_code=201
    )

    client = Client(api_key="test-api-key")
    topic_creator = client.topic()

    payload = {
        "name": "Test Topic",
        "description": "A test topic",
        "private": False
    }

    created_topic = topic_creator.create(payload)

    assert isinstance(created_topic, Topic)
    for attr in Topic._attributes:
        assert getattr(created_topic, attr) == topic_metadata[attr]


def test_topic_update(topic_api_call, httpx_mock):
    # Mock the update response
    updated_metadata = topic_metadata.copy()
    updated_metadata["name"] = "Updated Topic Name"
    updated_metadata["description"] = "Updated description"

    httpx_mock.add_response(
        method="PUT",
        url=f"https://www.data.gouv.fr/api/2/topics/{TOPIC_ID}/",
        json=updated_metadata,
        status_code=200
    )

    client = Client(api_key="test-api-key")
    topic = client.topic(TOPIC_ID)

    payload = {
        "name": "Updated Topic Name",
        "description": "Updated description"
    }

    response = topic.update(payload)

    assert response.status_code == 200
    assert topic.name == "Updated Topic Name"
    assert topic.description == "Updated description"


def test_topic_delete(topic_api_call, httpx_mock):
    # Mock the delete response
    httpx_mock.add_response(
        method="DELETE",
        url=f"https://www.data.gouv.fr/api/2/topics/{TOPIC_ID}/",
        status_code=204
    )

    client = Client(api_key="test-api-key")
    topic = client.topic(TOPIC_ID)

    response = topic.delete()

    assert response.status_code == 204
