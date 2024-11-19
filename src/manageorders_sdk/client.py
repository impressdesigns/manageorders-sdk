"""ManageOrders API client."""

from typing import Any

from httpx import Client, Response


class ManageOrdersClient:
    """ManageOrders API client."""

    def __init__(
        self,
        base_url: str,
        client_id: str,
        client_secret: str,
        timeout: float,
    ) -> None:
        """Initialize the ManageOrdersClient class."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.client = Client(
            base_url=base_url,
            timeout=timeout,
        )

    def _make_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Response:
        """Make a request to ManageOrders."""
        args: dict[str, str | dict[str, str]] = {
            "url": path,
            "method": method,
        }

        if params is not None:
            args["params"] = params

        if json is not None:
            args["json"] = json

        return self.client.request(**args)  # type: ignore[arg-type]
