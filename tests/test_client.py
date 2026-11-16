"""Tests for the ManageOrders client."""

import json
from datetime import date
from typing import Any

import pytest
from niquests import HTTPError, Response

from manageorders_sdk import ManageOrdersClient
from manageorders_sdk.models import Tracking, TrackingContainer

SIGN_IN = {"id_token": "token-1"}


def _response(status_code: int, body: dict[str, Any] | None = None) -> Response:
    """Build a niquests Response without touching the network."""
    response = Response()
    response.status_code = status_code
    response._content = json.dumps(body or {}).encode()  # noqa: SLF001 -- no public way to seed a canned body
    return response


class _SessionRecorder:
    """Stand-in for ``Session.request`` serving canned responses and recording calls."""

    def __init__(self, responses: list[Response]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    def request(self, **kwargs: Any) -> Response:  # noqa: ANN401 -- mirrors Session.request's open signature
        self.calls.append(kwargs)
        return self.responses.pop(0)


def _record(client: ManageOrdersClient, monkeypatch: pytest.MonkeyPatch, responses: list[Response]) -> _SessionRecorder:
    """Route the client's session requests through a recorder."""
    recorder = _SessionRecorder(responses)
    monkeypatch.setattr(client.session, "request", recorder.request)
    return recorder


def _tracking() -> TrackingContainer:
    """Build the tracking for one shipped box."""
    return TrackingContainer(
        api_source="tests",
        external_order_id="1001",
        tracking=Tracking(
            tracking="1Z999",
            date_shipped=date(2026, 11, 16),
            company="Impress Designs",
            name="Receiving",
            address1="1 Main St",
            address2="",
            city="Springfield",
            state="IL",
            postal_code="62701",
            country="US",
            cost=12.5,
            weight=3.0,
        ),
    )


def test_client_defaults() -> None:
    """A new client points at ManageOrders, keeps its login, and has no token yet."""
    username, secret = "user", "secret"
    client = ManageOrdersClient(username, secret)

    assert client.base_url == "https://manageordersapi.com"
    assert client.session.base_url == "https://manageordersapi.com"
    assert client.username == username
    assert client.password == secret
    assert client.token == ""


def test_upload_signs_in_then_sends_the_tracking_with_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """The first upload signs in, then pushes the tracking under ManageOrders' field names."""
    client = ManageOrdersClient("user", "secret")
    recorder = _record(client, monkeypatch, [_response(200, SIGN_IN), _response(200)])

    client.upload_tracking(_tracking())

    sign_in, upload = recorder.calls
    assert sign_in == {
        "method": "POST",
        "url": "/v1/manageorders/signin",
        "json": {"username": "user", "password": "secret"},
    }
    assert upload["method"] == "POST"
    assert upload["url"] == "/onsite/track-push"
    assert upload["headers"] == {"Authorization": "Bearer token-1"}
    assert upload["json"]["ExtOrderID"] == "1001"
    assert upload["json"]["Tracking"]["date_Shipped"] == "11/16/2026"


def test_a_second_upload_reuses_the_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """A token that has not expired is not asked for again."""
    client = ManageOrdersClient("user", "secret")
    recorder = _record(client, monkeypatch, [_response(200, SIGN_IN), _response(200), _response(200)])

    client.upload_tracking(_tracking())
    client.upload_tracking(_tracking())

    assert [call["url"] for call in recorder.calls] == [
        "/v1/manageorders/signin",
        "/onsite/track-push",
        "/onsite/track-push",
    ]


def test_a_refused_sign_in_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A sign-in ManageOrders refuses surfaces as an exception before anything is uploaded."""
    client = ManageOrdersClient("user", "wrong")
    recorder = _record(client, monkeypatch, [_response(401)])

    with pytest.raises(HTTPError):
        client.upload_tracking(_tracking())

    assert len(recorder.calls) == 1
