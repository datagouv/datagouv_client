import pytest
from unittest.mock import Mock, patch

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


@pytest.mark.parametrize(
    "responses,next_page_key,expected_data",
    [
        # Test simple next_page key
        (
            [
                {"data": [{"id": 1}, {"id": 2}], "next_page": "https://api.example.com/page2"},
                {"data": [{"id": 3}, {"id": 4}], "next_page": None},
            ],
            "next_page",
            [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}],
        ),
        # Test nested next_page key with dots
        (
            [
                {"data": [{"id": 1}], "links": {"next": "https://api.example.com/page2"}},
                {"data": [{"id": 2}], "links": {"next": None}},
            ],
            "links.next",
            [{"id": 1}, {"id": 2}],
        ),
        # Test single page (no pagination)
        (
            [{"data": [{"id": 1}, {"id": 2}], "next_page": None}],
            "next_page",
            [{"id": 1}, {"id": 2}],
        ),
        # Test missing next_page key
        (
            [{"data": [{"id": 1}]}],
            "next_page",
            [{"id": 1}],
        ),
        # Test deeply nested key
        (
            [
                {"data": [{"id": 1}], "meta": {"pagination": {"next": "https://api.example.com/page2"}}},
                {"data": [{"id": 2}], "meta": {"pagination": {"next": None}}},
            ],
            "meta.pagination.next",
            [{"id": 1}, {"id": 2}],
        ),
    ],
)
def test_get_all_from_api_query_pagination(responses, next_page_key, expected_data):
    client = Client()

    # Mock the session.get method
    mock_responses = []
    for response_data in responses:
        mock_response = Mock()
        mock_response.json.return_value = response_data
        mock_response.raise_for_status.return_value = None
        mock_responses.append(mock_response)

    with patch.object(client.session, 'get', side_effect=mock_responses):
        result = list(client.get_all_from_api_query("api/test", next_page=next_page_key))

    assert result == expected_data


def test_get_all_from_api_query_with_mask():
    client = Client()

    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"id": 1, "title": "test"}], "next_page": None}
    mock_response.raise_for_status.return_value = None

    with patch.object(client.session, 'get', return_value=mock_response) as mock_get:
        list(client.get_all_from_api_query("api/test", mask="data{id,title}"))

        # Verify the mask was added to headers
        mock_get.assert_called_once()
        headers = mock_get.call_args[1]['headers']
        assert headers['X-fields'] == "data{id,title},next_page"
