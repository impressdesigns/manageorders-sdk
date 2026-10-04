"""Testing the client."""

from manageorders_sdk import ManageOrdersClient


def test_client_defaults() -> None:
    """A new client points at ManageOrders, keeps its login, and has no token yet."""
    username, secret = "user", "secret"
    client = ManageOrdersClient(username, secret)

    assert client.base_url == "https://manageordersapi.com"
    assert client.username == username
    assert client.password == secret
    assert client.token == ""
