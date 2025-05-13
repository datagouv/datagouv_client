import os
import pytest
from unittest.mock import patch

import requests_mock

from conftest import DATASET_ID, RESOURCE_ID, resource_metadata_api1
from datagouv.base_object import BaseObject
from datagouv.client import Client
from datagouv.dataset import Dataset
from datagouv.resource import Resource, ResourceCreator


def test_resource_instance(static_resource_api2_call):
    assert isinstance(Client().resource(), ResourceCreator)
    assert isinstance(Client().resource(RESOURCE_ID), Resource)


def test_static_resource_instance_with_dataset_id(static_resource_api1_call):
    r = Client().resource(RESOURCE_ID, dataset_id=DATASET_ID)
    assert isinstance(r, Resource)
    assert r.filetype == "file"


def test_remote_resource_instance_with_dataset_id(remote_resource_api1_call):
    r = Client().resource(RESOURCE_ID, dataset_id=DATASET_ID)
    assert isinstance(r, Resource)
    assert r.filetype == "remote"


def test_resource_attributes_and_methods(static_resource_api2_call):
    client = Client()
    r = client.resource(RESOURCE_ID)
    with patch("requests.Session.get") as mock_func:
        r_from_response = Resource(
            RESOURCE_ID, dataset_id=DATASET_ID, _from_response=resource_metadata_api1
        )
        # when instanciating from a response, we don't call the API another time
        mock_func.assert_not_called()
    for attribute in (
        [
            "id",
            "uri",
            "front_url",
            "dataset",
        ]
        + Resource._attributes
        + [method for method in dir(BaseObject) if not method.startswith("__")]
    ):
        assert attribute in dir(r)
        assert attribute in dir(r_from_response)


def test_authentification_assertion():
    client = Client()
    with pytest.raises(PermissionError):
        client.resource().create_static(
            {"path": "path"}, {"title": "Titre"}, DATASET_ID
        )
    with pytest.raises(PermissionError):
        client.resource().create_remote({"url": "url", "title": "Titre"}, DATASET_ID)
    r_from_response = Resource(
        RESOURCE_ID, dataset_id=DATASET_ID, _from_response=resource_metadata_api1
    )
    with pytest.raises(PermissionError):
        r_from_response.delete()
    for method in ["update", "update_extras", "delete_extras"]:
        with pytest.raises(PermissionError):
            getattr(r_from_response, method)({})


def test_dataset(dataset_api_call):
    r_from_response = Resource(
        RESOURCE_ID, dataset_id=DATASET_ID, _from_response=resource_metadata_api1
    )
    assert isinstance(r_from_response.dataset(), Dataset)


def test_upload_file_into_remote(remote_resource_api2_call):
    client = Client(api_key="SUPER_SECRET")
    res = client.resource(RESOURCE_ID)
    assert res.filetype == "remote"
    with pytest.raises(ValueError):
        res.update({}, "path/to/file.csv")


def test_resource_no_fetch():
    # no fetch only if the dataset_id is given, otherwise we ping api/2
    with patch("requests.Session.get") as mock_func:
        r = Resource(RESOURCE_ID, DATASET_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(r, a, None) is None for a in Resource._attributes)
    assert r.uri


@pytest.mark.parametrize(
    "file_name",
    [
        "my_file.csv",
        None,
    ],
)
def test_resource_download(remote_resource_api1_call, file_name):
    r = Client().resource(RESOURCE_ID, dataset_id=DATASET_ID)
    with requests_mock.Mocker() as m:
        m.get(r.url, content=b"a,b,c\n1,2,3")
        r.download(file_name)
        local_name = file_name or f"{r.id}.{r.format}"
        with open(local_name, "r") as f:
            rows = f.readlines()
        assert rows[0] == "a,b,c\n"
        assert rows[1] == "1,2,3"
    os.remove(local_name)
