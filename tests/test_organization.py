from unittest.mock import patch

import pytest
import requests_mock
from conftest import (
    DATAGOUV_URL,
    ORGANIZATION_ID,
    OWNER_ID,
    dataset_metadata,
    organization_metadata,
)

from datagouv.base_object import BaseObject
from datagouv.client import Client
from datagouv.dataset import Dataset
from datagouv.organization import Organization, OrganizationCreator


def test_organization_instance(organization_api_call):
    assert isinstance(Client().organization(), OrganizationCreator)
    assert isinstance(Client().organization(ORGANIZATION_ID), Organization)


def test_organization_attributes_and_methods(organization_api_call):
    client = Client()
    o = client.organization(ORGANIZATION_ID)
    with patch("requests.Session.get") as mock_func:
        o_from_response = Organization(organization_metadata["id"], _from_response=organization_metadata)
        # when instanciating from a response, we don't call the API another time
        mock_func.assert_not_called()
    for attribute in (
        [
            "id",
            "uri",
            "front_url",
            "datasets",
            "create_dataset",
        ]
        + Organization._attributes
        + [method for method in dir(BaseObject) if not method.startswith("__")]
    ):
        assert attribute in dir(o)
        assert attribute in dir(o_from_response)


def test_authentification_assertion():
    client = Client()
    with pytest.raises(PermissionError):
        client.organization().create({"name": "Nom"})
    o_from_response = Organization(organization_metadata["id"], _from_response=organization_metadata)
    with pytest.raises(PermissionError):
        o_from_response.delete()
    for method in [
        "update",
        "update_extras",
        "delete_extras",
        "create_dataset",
    ]:
        with pytest.raises(PermissionError):
            getattr(o_from_response, method)({})

    # can't create a dataset from an organizaton and specify an organization or owner
    with pytest.raises(ValueError):
        o_from_response.create_dataset({"title": "Titre", "organization": ORGANIZATION_ID})
    with pytest.raises(ValueError):
        o_from_response.create_dataset({"title": "Titre", "owner": OWNER_ID})


def test_datasets():
    with requests_mock.Mocker() as m:
        m.get(
            f"{DATAGOUV_URL}api/1/organizations/{ORGANIZATION_ID}/datasets/",
            json={"data": [dataset_metadata], "next_page": None},
        )
        o_from_response = Organization(ORGANIZATION_ID, _from_response=organization_metadata)
        datasets = list(o_from_response.datasets())
        assert len(datasets) == 1
        assert isinstance(datasets[0], Dataset)


def test_organization_no_fetch():
    with patch("requests.Session.get") as mock_func:
        o = Organization(ORGANIZATION_ID, fetch=False)
        mock_func.assert_not_called()
    assert all(getattr(o, a, None) is None for a in Organization._attributes)
    assert o.uri
