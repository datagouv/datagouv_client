from unittest.mock import patch

from conftest import OWNER_ID, TOPIC_ID, elements_metadata, topic_metadata

from datagouv.base_object import BaseObject
from datagouv.client import Client
from datagouv.topic import Topic


def test_dataset_instance(topic_api_call):
    assert isinstance(Client().topic(TOPIC_ID), Topic)


def test_topic_attributes_and_methods(topic_api_call):
    client = Client()
    topic = client.topic(TOPIC_ID)
    with patch("httpx.Client.get") as mock_func:
        topic_from_response = Topic(topic.id, _from_response=topic_metadata)
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


def test_elements(topic_api_call, elements_api_call):
    topic = Topic(TOPIC_ID)
    elements = topic.elements
    assert len(elements) == len(elements_metadata["data"])


def test_datasets(topic_api_call, elements_api_call, dataset_catchall_api_call):
    topic = Topic(TOPIC_ID)
    datasets = topic.datasets
    assert len(datasets) == len(
        [
            e
            for e in elements_metadata["data"]
            if e["element"] and e["element"]["class"] == "Dataset"
        ]
    )


def test_topic_has_owner():
    owner = {"id": OWNER_ID}
    topic_with_owner = Topic(
        TOPIC_ID,
        _from_response=topic_metadata | {"organization": None} | {"owner": owner},
    )
    assert topic_with_owner.organization is None
    assert topic_with_owner.owner == owner
