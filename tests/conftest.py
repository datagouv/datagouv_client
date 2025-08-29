import json

import httpx  # noqa
import pytest

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
def dataset_api_call(httpx_mock):
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/",
        json=dataset_metadata,
        is_reusable=True,
    )
    yield httpx_mock


@pytest.fixture
def static_resource_api1_call(httpx_mock):
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/",
        json=resource_metadata_api1,
        is_reusable=True,
    )
    yield httpx_mock


@pytest.fixture
def remote_resource_api1_call(httpx_mock):
    remote_metadata = resource_metadata_api1
    remote_metadata["filetype"] = "remote"
    remote_metadata["url"] = "https://example.com/file.csv"
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/",
        json=remote_metadata,
        is_reusable=True,
    )
    yield httpx_mock


@pytest.fixture
def static_resource_api2_call(httpx_mock):
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/",
        json=resource_metadata_api2,
        is_reusable=True,
    )
    yield httpx_mock


@pytest.fixture
def remote_resource_api2_call(httpx_mock):
    remote_metadata = resource_metadata_api2
    remote_metadata["resource"]["filetype"] = "remote"
    remote_metadata["resource"]["url"] = "https://example.com/file.csv"
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/",
        json=remote_metadata,
        is_reusable=True,
    )
    yield httpx_mock


@pytest.fixture
def organization_api_call(httpx_mock):
    httpx_mock.add_response(
        url=f"{DATAGOUV_URL}api/1/organizations/{ORGANIZATION_ID}/",
        json=organization_metadata,
        is_reusable=True,
    )
    yield httpx_mock
