import json

import pytest
from rest_framework.test import APIClient

from apps.core.exceptions import ZillowClientError
from clients.zillow_client import ZillowClient


def test_property_html_single_request(httpx_mock):
    cache = json.dumps({"property-query": {"property": {"zpid": 123, "city": "Seattle"}}})
    data = {"props": {"pageProps": {"componentProps": {"gdpClientCache": cache}}}}
    httpx_mock.add_response(
        url="https://www.zillow.com/homedetails/123_zpid/",
        text='<script id="__NEXT_DATA__" type="application/json">' + json.dumps(data) + "</script>",
    )
    with ZillowClient() as client:
        client.request_delay = 0
        assert client.get_property_from_page(123) == {"zpid": 123, "city": "Seattle"}
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.parametrize("status", [400, 403, 404, 429])
def test_terminal_failures_not_retried(httpx_mock, status):
    httpx_mock.add_response(status_code=status)
    with ZillowClient() as client, pytest.raises(ZillowClientError):
        client.request_delay = 0
        client.get_property_from_page(123)
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.parametrize("resource", ["schools", "nearby", "comparables", "rent-zestimate"])
def test_new_resources(httpx_mock, resource, settings):
    settings.ZILLOW_CLIENT = {"REQUEST_DELAY": 0}
    httpx_mock.add_response(
        url="https://www.zillow.com/graphql/",
        method="POST",
        json={"data": {"property": {"zpid": 123}}},
    )
    response = APIClient().get(f"/api/v1/properties/123/{resource}/")
    assert response.status_code == 200
    assert response.json()["data"]["property"]["zpid"] == 123


def test_invalid_page_is_400():
    response = APIClient().post(
        "/api/v1/search/", {"query": "Seattle", "page": "bad"}, format="json"
    )
    assert response.status_code == 400


def test_ingestion_requires_staff():
    assert APIClient().post("/api/v1/ingest/property/", {"zpid": 123}).status_code == 403
