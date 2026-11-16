"""Interacting with ManageOrders API."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import niquests

if TYPE_CHECKING:
    from .models import Order, TrackingContainer


class ManageOrdersClient:
    """A class wrapping interaction with ManageOrders API."""

    def __init__(
        self,
        username: str,
        password: str,
        timeout: float = 5.0,
    ) -> None:
        """Initialize the ManageOrdersClient class.

        Parameters
        ----------
        username
            The ManageOrders account's username.
        password
            The ManageOrders account's password.
        timeout
            The request timeout in seconds.
        """
        self.base_url = "https://manageordersapi.com"
        self.username = username
        self.password = password
        self.token = ""
        self.token_expires_at = datetime.now(tz=UTC)
        self.session = niquests.Session(
            base_url=self.base_url,
            timeout=timeout,
        )

    def _update_token(self) -> None:
        """Update the OAUTH token."""
        if self.token_expires_at > datetime.now(tz=UTC):
            return

        auth_dict = {
            "username": self.username,
            "password": self.password,
        }
        response = self.session.request(method="POST", url="/v1/manageorders/signin", json=auth_dict)
        response.raise_for_status()
        data = response.json()
        self.token = data["id_token"]
        self.token_expires_at = datetime.now(tz=UTC) + timedelta(hours=1)

    def _make_request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> niquests.Response:
        """Make a request to ManageOrders."""
        self._update_token()

        args: dict[str, Any] = {
            "url": path,
            "method": method,
            "headers": {"Authorization": "Bearer " + self.token},
        }

        if params is not None:
            args["params"] = params

        if json is not None:
            args["json"] = json

        return self.session.request(**args)

    def upload_order(
        self,
        order: Order,
    ) -> niquests.Response:
        """Upload an order to ManageOrders."""
        return self._make_request("POST", "/onsite/order-push", json=order.model_dump(by_alias=True, exclude_none=True))

    def upload_tracking(
        self,
        tracking_data: TrackingContainer,
    ) -> niquests.Response:
        """Upload tracking data to ManageOrders."""
        return self._make_request(
            "POST",
            "/onsite/track-push",
            json=tracking_data.model_dump(by_alias=True, exclude_none=True),
        )
