import json

import pytest
import requests_mock

DATASET_ID = "0123456789abcdef01234567"
RESOURCE_ID = "aaaaaaaa-1111-bbbb-2222-cccccccccccc"
ORGANIZATION_ID = "646b7187b50b2a93b1ae3d45"
OWNER_ID = "637b5c6eef50bb3f5a97b24f"
DATAGOUV_URL = "https://www.data.gouv.fr/"

with open("tests/dataset_metadata.json", "r") as f:
    dataset_metadata = json.load(f)

with open("tests/resource_metadata_api1.json", "r") as f:
    resource_metadata_api1 = json.load(f)

with open("tests/resource_metadata_api2.json", "r") as f:
    resource_metadata_api2 = json.load(f)

with open("tests/organization_metadata.json", "r") as f:
    organization_metadata = json.load(f)


@pytest.fixture
def dataset_api_call():
    with requests_mock.Mocker() as m:
        m.get(f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/", json=dataset_metadata)
        yield m


@pytest.fixture
def static_resource_api1_call():
    with requests_mock.Mocker() as m:
        m.get(
            f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/",
            json=resource_metadata_api1,
        )
        yield m


@pytest.fixture
def remote_resource_api1_call():
    remote_metadata = resource_metadata_api1
    remote_metadata["filetype"] = "remote"
    remote_metadata["url"] = "https://example.com/file.csv"
    with requests_mock.Mocker() as m:
        m.get(
            f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/",
            json=remote_metadata,
        )
        yield m


@pytest.fixture
def static_resource_api2_call():
    with requests_mock.Mocker() as m:
        m.get(
            f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/",
            json=resource_metadata_api2,
        )
        yield m


@pytest.fixture
def remote_resource_api2_call():
    remote_metadata = resource_metadata_api2
    remote_metadata["resource"]["filetype"] = "remote"
    remote_metadata["resource"]["url"] = "https://example.com/file.csv"
    with requests_mock.Mocker() as m:
        m.get(
            f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/",
            json=remote_metadata,
        )
        yield m


@pytest.fixture
def organization_api_call():
    with requests_mock.Mocker() as m:
        m.get(f"{DATAGOUV_URL}api/1/organizations/{ORGANIZATION_ID}/", json=organization_metadata)
        yield m
