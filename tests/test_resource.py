import os
from io import BytesIO
from unittest.mock import patch

import httpx  # noqa
import pytest
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
    with patch("httpx.Client.get") as mock_func:
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
        client.resource().create_static({"path": "path"}, {"title": "Titre"}, DATASET_ID)
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
    assert isinstance(r_from_response.dataset, Dataset)


def test_upload_file_into_remote(remote_resource_api2_call):
    client = Client(api_key="SUPER_SECRET")
    res = client.resource(RESOURCE_ID)
    assert res.filetype == "remote"
    with pytest.raises(ValueError):
        res.update({}, "path/to/file.csv")


def test_resource_no_fetch():
    # no fetch only if the dataset_id is given, otherwise we ping api/2
    with patch("httpx.Client.get") as mock_func:
        r = Resource(RESOURCE_ID, DATASET_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(r, a, None) is None for a in Resource._attributes)
    assert r.uri


@pytest.mark.parametrize(
    "file_name, custom_url, headers, expected_name",
    [
        ("my_file.csv", None, {}, "my_file.csv"),
        (
            None,
            "https://api.insee.fr/melodi/file/DS_ESTIMATION_POPULATION/DS_ESTIMATION_POPULATION_CSV_FR",
            {
                "content-length": "100",
                "content-disposition": 'inline; filename="file.csv"',
            },
            "file.csv",
        ),
        (
            None,
            "https://api.insee.fr/melodi/file/DS_ESTIMATION_POPULATION/DS_ESTIMATION_POPULATION_CSV_FR",
            {},
            f"{RESOURCE_ID}.csv",
        ),
    ],
)
def test_resource_download(
    remote_resource_api1_call,
    file_name,
    custom_url,
    headers,
    expected_name,
    httpx_mock,
):
    r = Client().resource(RESOURCE_ID, dataset_id=DATASET_ID)
    if custom_url:
        r.url = custom_url
        httpx_mock.add_response(
            method="HEAD",
            url=r.url,
            status_code=200,
            headers=headers,
        )
    httpx_mock.add_response(
        method="GET",
        url=r.url,
        status_code=200,
        content=b"a,b,c\n1,2,3",
    )
    local_name = r.download(file_name)
    assert local_name.as_posix() == expected_name
    with open(local_name, "r") as f:
        rows = f.readlines()
    assert rows[0] == "a,b,c\n"
    assert rows[1] == "1,2,3"
    os.remove(local_name)


def test_iter_download_streams_bytes(httpx_mock):
    r = Resource("id", dataset_id="ds", fetch=False)
    r.url = "https://example.com/file.csv"

    payload = b"a,b,c\n1,2,3\n"

    httpx_mock.add_response(
        method="GET",
        url=r.url,
        content=payload,
        status_code=200,
    )

    out = b"".join(r._iter_download(chunk_size=4))
    assert out == payload


def test_iter_download_raises_on_http_error(httpx_mock):
    r = Resource("id", dataset_id="ds", fetch=False)
    r.url = "https://example.com/missing.csv"

    httpx_mock.add_response(
        method="GET",
        url=r.url,
        status_code=404,
        text="not found",
    )

    with pytest.raises(Exception):
        next(r._iter_download())  # force iteration so the request actually happens


def test_download_buffer_happy_path(monkeypatch):
    # Test when good parameters are provided, it returns the expected buffer
    r = Resource("id", dataset_id="ds", fetch=False)
    r.url = "https://example.com/file.csv"

    chunks = [b"a,b,c\n", b"1,2,3\n"]

    def fake_iter_download(*, chunk_size=8192, **kwargs):
        assert chunk_size == 4
        assert kwargs == {"timeout": 5.0}
        yield from chunks

    monkeypatch.setattr(r, "_iter_download", fake_iter_download)

    buf = r.download_buffer(chunk_size=4, max_mib=1, timeout=5.0)

    assert isinstance(buf, BytesIO)
    assert buf.tell() == 0
    assert buf.read() == b"".join(chunks)


def test_download_buffer_raises_when_too_large(monkeypatch):
    # Test the responses too large raise an error
    r = Resource("id", dataset_id="ds", fetch=False)
    r.url = "https://example.com/big.bin"

    chunks = [b"x" * 600, b"y" * 600]  # total 1200 bytes

    def fake_iter_download(*, chunk_size=8192, **kwargs):
        yield from chunks

    monkeypatch.setattr(r, "_iter_download", fake_iter_download)

    with pytest.raises(ValueError, match=r"Response too large"):
        r.download_buffer(max_mib=0.001)  # about 1048 bytes limit


def test_download_buffer_no_limit_when_max_mib_none(monkeypatch):
    # Test we can download larger files when the limit is set to None
    r = Resource("id", dataset_id="ds", fetch=False)
    r.url = "https://example.com/huge.bin"

    chunks = [b"x" * 10_000, b"y" * 10_000]

    def fake_iter_download(*, chunk_size=8192, **kwargs):
        yield from chunks

    monkeypatch.setattr(r, "_iter_download", fake_iter_download)

    buf = r.download_buffer(max_mib=None)
    assert buf.read() == b"".join(chunks)


@pytest.mark.parametrize(
    "method,kwargs",
    [
        (
            "create_static",
            {
                "payload": {"title": "New static resource"},
                "file_to_upload": "tests/resource_metadata_api1.json",
                "dataset_id": DATASET_ID,
            },
        ),
        (
            "create_remote",
            {
                "payload": {"title": "New remote resource"},
                "dataset_id": DATASET_ID,
            },
        ),
    ],
)
def test_resource_create(httpx_mock, method, kwargs):
    # Mock the API response for resource creation
    httpx_mock.add_response(
        method="POST",
        url=(
            f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"
            + ("resources/" if "remote" in method else "upload/")
        ),
        json=resource_metadata_api1,
        status_code=201,
    )
    if "static" in method:
        httpx_mock.add_response(
            method="PUT",
            url=(
                f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}"
                f"/resources/{resource_metadata_api1['id']}/"
            ),
            json=resource_metadata_api1,
            status_code=200,
        )

    client = Client(api_key="test-api-key")

    created_resource = getattr(client.resource(), method)(**kwargs)

    assert isinstance(created_resource, Resource)
    for attr in Resource._attributes:
        assert getattr(created_resource, attr) == resource_metadata_api1[attr]


def test_resource_update(static_resource_api2_call, httpx_mock):
    updated_metadata = resource_metadata_api1.copy()
    payload = {
        "title": "Updated Resource Title",
        "description": "Updated description",
    }

    client = Client(api_key="test-api-key")
    resource = client.resource(RESOURCE_ID)

    # Mock the update response
    httpx_mock.add_response(
        method="PUT",
        url=f"https://www.data.gouv.fr/api/1/datasets/{resource.dataset_id}/resources/{resource.id}/",
        json=updated_metadata | payload,
        status_code=200,
    )

    response = resource.update(payload)

    assert response.status_code == 200
    for attr in payload.keys():
        assert getattr(resource, attr) == payload[attr]


def test_resource_delete(static_resource_api2_call, httpx_mock):
    client = Client(api_key="test-api-key")
    resource = client.resource(RESOURCE_ID)

    # Mock the delete response
    httpx_mock.add_response(
        method="DELETE",
        url=f"https://www.data.gouv.fr/api/1/datasets/{resource.dataset_id}/resources/{resource.id}/",
        status_code=204,
    )

    response = resource.delete()

    assert response.status_code == 204
