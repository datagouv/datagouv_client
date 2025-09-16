import pytest

from datagouv.client import Client


@pytest.mark.parametrize(
    "args",
    [
        ("www", None, False, False),
        ("www", "secret", True, False),
        ("demo", "secret", True, False),
        ("dev", "secret", True, False),
        ("ods", None, None, True),
    ],
)
def test_client_types(args):
    env, api_key, auth, should_raise = args
    if should_raise:
        with pytest.raises(ValueError):
            Client(env)
    else:
        client = Client(env, api_key)
        assert client._authenticated == auth
        assert all(
            a in dir(client)
            for a in [
                "_authenticated",
                "_envs",
                "base_url",
                "dataset",
                "get_all_from_api_query",
                "resource",
                "session",
            ]
        )


@pytest.mark.parametrize(
    "args",
    [
        ("api/1/datasets/", None, None),
        (
            "api/1/datasets/",
            "data{id,title,created_at}",
            ["id", "title", "created_at"],
        ),
    ],
)
def test_get_all(args):
    # is there a good way to mock this so that we don't call the API?
    query, mask, fields = args
    client = Client()
    for idx, data in enumerate(
        client.get_all_from_api_query(
            query,
            mask=mask,
        )
    ):
        if idx > 3:
            break
        if mask:
            assert list(sorted(fields)) == list(sorted(data.keys()))
        assert data["id"]


def test_build_url():
    client = Client()
    assert client._build_url("/api/2/coucou") == "https://www.data.gouv.fr/api/2/coucou"
    assert client._build_url("https://www.data.gouv.fr/api/2/coucou") == "https://www.data.gouv.fr/api/2/coucou"
    assert client._build_url("api/2/coucou") == "https://www.data.gouv.fr/api/2/coucou"
