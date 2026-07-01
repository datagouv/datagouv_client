from unittest.mock import patch

import pytest
from conftest import (
    API_ID,
    DATAGOUV_URL,
    ORGANIZATION_ID,
    OWNER_ID,
    api_metadata,
    dataset_metadata,
    organization_metadata,
)

from datagouv.api.api import API
from datagouv.api.client import Client
from datagouv.api.dataset import Dataset
from datagouv.api.organization import Organization
from datagouv.utils.base_object import BaseObject


def test_api_instance(api_api_call):
    assert isinstance(Client().api(API_ID), API)


def test_api_attributes_and_methods(api_api_call):
    client = Client()
    a = client.api(API_ID)
    with patch("niquests.Session.get") as mock_func:
        a_from_response = API(api_metadata["id"], _from_response=api_metadata)
        mock_func.assert_not_called()
    for attribute in (
        ["id", "uri", "front_url", "organization_id", "associated_datasets"]
        + API._attributes
        + [method for method in dir(BaseObject) if not method.startswith("__")]
    ):
        assert attribute in dir(a)
        assert attribute in dir(a_from_response)


def test_api_no_fetch():
    with patch("niquests.Session.get") as mock_func:
        a = API(API_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(a, attr, None) is None for attr in API._attributes)
    assert a.uri


def test_authentication_assertion():
    client = Client()
    with pytest.raises(PermissionError):
        client.create_API({"title": "Test API"})
    a = API(API_ID, _from_response=api_metadata)
    with pytest.raises(PermissionError):
        a.delete()
    with pytest.raises(PermissionError):
        a.update({})
    with pytest.raises(PermissionError):
        a.update_extras({})
    with pytest.raises(PermissionError):
        a.delete_extras([])


def test_api_update(api_api_call, niquests_mock):
    updated_metadata = api_metadata.copy()
    payload = {"title": "Updated API Title", "description": "Updated description"}
    niquests_mock.patch(f"{DATAGOUV_URL}api/1/dataservices/{API_ID}/").respond(
        json=updated_metadata | payload,
        status_code=200,
    )
    client = Client(api_key="test-api-key")
    a = client.api(API_ID)
    response = a.update(payload)
    assert response.status_code == 200
    for attr in payload:
        assert getattr(a, attr) == payload[attr]


def test_api_update_invalid_payload():
    client = Client(api_key="test-api-key")
    a = API(API_ID, _client=client, _from_response=api_metadata)
    with pytest.raises(TypeError):
        a.update("not a dict")


def test_api_create(niquests_mock):
    niquests_mock.post(f"{DATAGOUV_URL}api/1/dataservices/").respond(
        json=api_metadata,
        status_code=201,
    )
    client = Client(api_key="test-api-key")
    created = client.create_API({"title": "New API", "organization": ORGANIZATION_ID})
    assert isinstance(created, API)
    for attr in API._attributes:
        assert getattr(created, attr) == api_metadata[attr]


def test_api_delete(api_api_call, niquests_mock):
    niquests_mock.delete(f"{DATAGOUV_URL}api/1/dataservices/{API_ID}/").respond(status_code=204)
    client = Client(api_key="test-api-key")
    a = client.api(API_ID)
    response = a.delete()
    assert response.status_code == 204


def test_organization_id():
    a = API(API_ID, _from_response=api_metadata)
    assert a.organization_id == ORGANIZATION_ID


def test_associated_datasets(niquests_mock):
    niquests_mock.get(
        f"{DATAGOUV_URL}api/1/datasets/?dataservice={API_ID}"
    ).respond(json={"data": [dataset_metadata], "next_page": None})
    a = API(API_ID, _from_response=api_metadata)
    datasets = list(a.associated_datasets)
    assert len(datasets) == 1
    assert isinstance(datasets[0], Dataset)


def test_associated_datasets_slug():
    slug = "my-api-slug"
    a = API(slug, _from_response=api_metadata)
    with pytest.raises(Exception, match="slug"):
        list(a.associated_datasets)


def test_organization_create_api(niquests_mock):
    niquests_mock.post(f"{DATAGOUV_URL}api/1/dataservices/").respond(
        json=api_metadata,
        status_code=201,
    )
    client = Client(api_key="test-api-key")
    org = Organization(ORGANIZATION_ID, _client=client, _from_response=organization_metadata)
    created = org.create_API({"title": "New API"})
    assert isinstance(created, API)


def test_organization_create_api_org_override():
    org = Organization(ORGANIZATION_ID, _from_response=organization_metadata)
    with pytest.raises(ValueError):
        org.create_API({"title": "New API", "organization": ORGANIZATION_ID})
    with pytest.raises(ValueError):
        org.create_API({"title": "New API", "owner": OWNER_ID})


def test_client_api_methods():
    client = Client()
    assert hasattr(client, "api")
    assert hasattr(client, "create_API")
