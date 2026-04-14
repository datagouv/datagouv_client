import os
import shutil
from unittest.mock import Mock, patch

import httpx  # noqa
import pytest
from conftest import DATASET_ID, OWNER_ID, dataset_metadata

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
    with patch("httpx.Client.get") as mock_func:
        d_from_response = Dataset(dataset_metadata["id"], _from_response=dataset_metadata)
        # when instanciating from a response, we don't call the API another time
        mock_func.assert_not_called()
    for attribute in (
        [
            "id",
            "uri",
            "front_url",
            "resources",
            "organization",
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
        d_from_response.create_static({"path": "path"}, {"title": "Titre"}, dataset_id="aaa")
    with pytest.raises(ValueError):
        d_from_response.create_remote({"title": "Titre"}, dataset_id="aaa")


def test_resources():
    with patch("httpx.Client.get") as mock_func:
        d_from_response = Dataset(DATASET_ID, _from_response=dataset_metadata)
        assert len(d_from_response.resources) == len(dataset_metadata["resources"])
        assert all(isinstance(r, Resource) for r in d_from_response.resources)
        # not calling the API when building the resources
        mock_func.assert_not_called()


def test_dataset_no_fetch():
    with patch("httpx.Client.get") as mock_func:
        d = Dataset(DATASET_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(d, a, None) is None for a in Dataset._attributes)
    assert d.uri


def test_download_dataset_resources(dataset_api_call, httpx_mock):
    d = Dataset(DATASET_ID)
    folder = "data_test"
    os.mkdir(folder)
    for res in d.resources:
        # only mocking the resources we download, otherwise httpx raises
        if res.type == "main":
            httpx_mock.add_response(
                url=res.url,
                content=b"a,b,c\n1,2,3",
                is_reusable=True,
            )
    d.download_resources(folder=folder, resources_types=["main"])
    assert len(os.listdir(folder)) == len([r for r in d.resources if r.type == "main"])
    shutil.rmtree(folder)


def test_dataset_has_owner():
    owner = {"id": OWNER_ID}
    dataset_with_owner = Dataset(
        DATASET_ID,
        _from_response=dataset_metadata | {"organization": None} | {"owner": owner},
    )
    assert dataset_with_owner.organization is None
    assert dataset_with_owner.owner == owner


def test_dataset_create(httpx_mock):
    # Mock the API response for dataset creation
    httpx_mock.add_response(
        method="POST",
        url="https://www.data.gouv.fr/api/1/datasets/",
        json=dataset_metadata,
        status_code=201,
    )

    client = Client(api_key="test-api-key")

    payload = {
        "title": "New dataset",
        "description": "A new dataset",
        "organization": "646b7187b50b2a93b1ae3d45",
    }

    created_dataset = client.dataset().create(payload)

    assert isinstance(created_dataset, Dataset)
    for attr in Dataset._attributes:
        assert getattr(created_dataset, attr) == dataset_metadata[attr]


def test_dataset_update(dataset_api_call, httpx_mock):
    # Mock the update response
    updated_metadata = dataset_metadata.copy()
    payload = {
        "title": "Updated Dataset Title",
        "description": "Updated description",
    }
    httpx_mock.add_response(
        method="PUT",
        url=f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/",
        json=updated_metadata | payload,
        status_code=200,
    )

    client = Client(api_key="test-api-key")
    dataset = client.dataset(DATASET_ID)

    response = dataset.update(payload)

    assert response.status_code == 200
    for attr in payload.keys():
        assert getattr(dataset, attr) == payload[attr]


def test_dataset_delete(dataset_api_call, httpx_mock):
    # Mock the delete response
    httpx_mock.add_response(
        method="DELETE",
        url=f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/",
        status_code=204,
    )

    client = Client(api_key="test-api-key")
    dataset = client.dataset(DATASET_ID)

    response = dataset.delete()

    assert response.status_code == 204


def custom_sort(res_list: list[Resource]):
    keys = [
        {"key": r.title[::-1], "res": r}
        for r in res_list
    ]
    return [item["res"] for item in sorted(keys, key=lambda k: k["key"])]


@pytest.mark.parametrize(
    "kwarg, success",
    [
        ({"by": "title.desc"}, True),
        ({"by": "created_at.asc"}, True),
        ({"sort_function": custom_sort}, True),
        ({"by": "created_at.tri"}, False),
        ({"by": "asc"}, False),
        ({}, False),
        ({"sort_function": lambda r_list: r_list + [r_list[-1]]}, False),
        ({"sort_function": lambda r_list: r_list[:-1]}, False),
    ],
)
def test_sort_resources(kwarg, success, dataset_api_call):
    client = Client(api_key="test-api-key")
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    dataset = client.dataset(DATASET_ID)

    if not success:
        with pytest.raises(Exception):
            dataset.sort_resources(**kwarg)
        return

    if "by" in kwarg:
        key, order = kwarg["by"].split(".")
        expected = sorted(
            dataset.resources,
            key=lambda r: getattr(r, key)
        )
        if order == "desc":
            expected = reversed(expected)
        expected = [{"id": r.id} for r in expected]
    else:
        expected = [{"id": r.id} for r in kwarg["sort_function"](dataset.resources)]

    with patch.object(client.session, "put") as mock_put:
        dataset.sort_resources(**kwarg)
        # Verify the mask was added to headers
        mock_put.assert_called_with(
            dataset.uri + "resources/",
            json=expected,
        )
