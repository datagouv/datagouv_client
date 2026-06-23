import json
import re
from copy import deepcopy

import pytest

DATASET_ID = "0123456789abcdef01234567"
RESOURCE_ID = "aaaaaaaa-1111-bbbb-2222-cccccccccccc"
ORGANIZATION_ID = "646b7187b50b2a93b1ae3d45"
OWNER_ID = "637b5c6eef50bb3f5a97b24f"
DATAGOUV_URL = "https://www.data.gouv.fr/"
TOPIC_ID = "68b6e6dbdac745f47d4ff6e0"

with open("tests/dataset_metadata.json", "r") as f:
    dataset_metadata = json.load(f)

with open("tests/resource_metadata_api1.json", "r") as f:
    tabular_resource_metadata_api1 = json.load(f)
resource_metadata_api1 = tabular_resource_metadata_api1 | {"preview_url": None}

with open("tests/resource_metadata_api2.json", "r") as f:
    tabular_resource_metadata_api2 = json.load(f)
resource_metadata_api2 = deepcopy(tabular_resource_metadata_api2)
resource_metadata_api2["resource"]["preview_url"] = None

with open("tests/organization_metadata.json", "r") as f:
    organization_metadata = json.load(f)

with open("tests/topic_metadata.json", "r") as f:
    topic_metadata = json.load(f)

with open("tests/elements_metadata.json", "r") as f:
    elements_metadata = json.load(f)

with open("tests/tabular_api_data.json", "r") as f:
    tabular_api_data = json.load(f)

with open("tests/tabular_api_profile.json", "r") as f:
    tabular_api_profile = json.load(f)


@pytest.fixture
def dataset_api_call(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/").respond(json=dataset_metadata)
    yield niquests_mock


@pytest.fixture
def dataset_catchall_api_call(niquests_mock):
    niquests_mock.get(re.compile(f"{DATAGOUV_URL}api/1/datasets/.*?/")).respond(
        json=dataset_metadata
    )
    yield niquests_mock


@pytest.fixture
def topic_api_call(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/2/topics/{TOPIC_ID}/").respond(json=topic_metadata)
    yield niquests_mock


@pytest.fixture
def elements_api_call(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/2/topics/{TOPIC_ID}/elements/").respond(
        json=elements_metadata
    )
    yield niquests_mock


@pytest.fixture
def static_resource_api1_call(niquests_mock):
    niquests_mock.get(
        f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/"
    ).respond(json=resource_metadata_api1)
    yield niquests_mock


@pytest.fixture
def remote_resource_api1_call(niquests_mock):
    remote_metadata = deepcopy(resource_metadata_api1)
    remote_metadata["filetype"] = "remote"
    remote_metadata["url"] = "https://example.com/file.csv"
    niquests_mock.get(
        f"{DATAGOUV_URL}api/1/datasets/{DATASET_ID}/resources/{RESOURCE_ID}/"
    ).respond(json=remote_metadata)
    yield niquests_mock


@pytest.fixture
def static_resource_api2_call(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/").respond(
        json=resource_metadata_api2
    )
    yield niquests_mock


@pytest.fixture
def remote_resource_api2_call(niquests_mock):
    remote_metadata = resource_metadata_api2
    remote_metadata["resource"]["filetype"] = "remote"
    remote_metadata["resource"]["url"] = "https://example.com/file.csv"
    niquests_mock.get(f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/").respond(
        json=remote_metadata
    )
    yield niquests_mock


@pytest.fixture
def organization_api_call(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/1/organizations/{ORGANIZATION_ID}/").respond(
        json=organization_metadata
    )
    yield niquests_mock


@pytest.fixture
def tabular_resource_api_calls(niquests_mock):
    niquests_mock.get(f"{DATAGOUV_URL}api/2/datasets/resources/{RESOURCE_ID}/").respond(
        json=tabular_resource_metadata_api2
    )
    niquests_mock.get(
        f"https://tabular-api.data.gouv.fr/api/resources/{RESOURCE_ID}/profile/"
    ).respond(json=tabular_api_profile)
    yield niquests_mock
