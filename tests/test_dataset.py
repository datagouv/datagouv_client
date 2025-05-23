import os
import pytest
import shutil
from unittest.mock import patch

import requests_mock

from conftest import DATASET_ID, dataset_metadata
from datagouv.base_object import BaseObject
from datagouv.client import Client
from datagouv.dataset import Dataset, DatasetCreator
from datagouv.resource import Resource, ResourceCreator


def test_dataset_instance(dataset_api_call):
    assert isinstance(Client().dataset(), DatasetCreator)
    assert isinstance(Client().dataset(DATASET_ID), Dataset)


def test_dataset_attributes_and_methods(dataset_api_call):
    client = Client()
    d = client.dataset(DATASET_ID)
    with patch("requests.Session.get") as mock_func:
        d_from_response = Dataset(
            dataset_metadata["id"], _from_response=dataset_metadata
        )
        # when instanciating from a response, we don't call the API another time
        mock_func.assert_not_called()
    for attribute in (
        [
            "id",
            "uri",
            "front_url",
            "resources",
        ]
        + Dataset._attributes
        + [method for method in dir(BaseObject) if not method.startswith("__")]
        + [method for method in dir(ResourceCreator) if not method.startswith("__")]
    ):
        assert attribute in dir(d)
        assert attribute in dir(d_from_response)


def test_authentification_assertion():
    client = Client()
    with pytest.raises(PermissionError):
        client.dataset().create({"title": "Titre"})
    d_from_response = Dataset(DATASET_ID, _from_response=dataset_metadata)
    with pytest.raises(PermissionError):
        d_from_response.delete()
    for method in [
        "update",
        "update_extras",
        "delete_extras",
        "create_remote",
    ]:
        with pytest.raises(PermissionError):
            getattr(d_from_response, method)({})
    with pytest.raises(PermissionError):
        d_from_response.create_static({"path": "path"}, {"title": "Titre"})

    # can't create a resource from a dataset and specify a dataset_id
    with pytest.raises(ValueError):
        d_from_response.create_static(
            {"path": "path"}, {"title": "Titre"}, dataset_id="aaa"
        )
    with pytest.raises(ValueError):
        d_from_response.create_remote({"title": "Titre"}, dataset_id="aaa")


def test_resources():
    with patch("requests.Session.get") as mock_func:
        d_from_response = Dataset(DATASET_ID, _from_response=dataset_metadata)
        assert len(d_from_response.resources) == len(dataset_metadata["resources"])
        assert all(isinstance(r, Resource) for r in d_from_response.resources)
        # not calling the API when building the resources
        mock_func.assert_not_called()


def test_dataset_no_fetch():
    with patch("requests.Session.get") as mock_func:
        d = Dataset(DATASET_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(d, a, None) is None for a in Dataset._attributes)
    assert d.uri


def test_download_dataset_resources(dataset_api_call):
    d = Dataset(DATASET_ID)
    folder = "data_test"
    os.mkdir(folder)
    with requests_mock.Mocker() as m:
        for res in d.resources:
            m.get(res.url, content=b"a,b,c\n1,2,3")
        d.download_resources(folder=folder, resources_types=["main"])
    assert len(os.listdir(folder)) == len([r for r in d.resources if r.type == "main"])
    shutil.rmtree(folder)
