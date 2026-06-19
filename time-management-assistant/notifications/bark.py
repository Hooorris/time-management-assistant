from urllib.parse import quote

import httpx

from notifications.base import NotificationMessage, NotificationResult


class BarkNotifier:
    channel = "bark"

    def __init__(
        self,
        *,
        server_url: str = "https://api.day.app",
        device_key: str,
        sound: str | None = None,
        group: str | None = None,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.device_key = device_key
        self.sound = sound
        self.group = group
        self.timeout_seconds = timeout_seconds
        self.client = client

    def send(self, message: NotificationMessage) -> NotificationResult:
        if message.channel != self.channel:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=f"Bark notifier cannot send channel: {message.channel}",
            )
        if not self.device_key:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message="BARK_DEVICE_KEY is required.",
            )

        url = self._build_url(message)
        params = self._build_params(message)
        try:
            if self.client:
                response = self.client.get(url, params=params)
            else:
                with httpx.Client(timeout=self.timeout_seconds) as client:
                    response = client.get(url, params=params)
        except httpx.HTTPError as exc:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=str(exc),
            )

        body = response.text[:500] if response.text else None
        if response.status_code < 200 or response.status_code >= 300:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=f"Bark HTTP request failed with status {response.status_code}.",
                status_code=response.status_code,
                response_body=body,
            )

        api_error = self._extract_api_error(response)
        if api_error:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=api_error,
                status_code=response.status_code,
                response_body=body,
            )

        return NotificationResult(
            success=True,
            channel=self.channel,
            status_code=response.status_code,
            response_body=body,
        )

    def _build_url(self, message: NotificationMessage) -> str:
        key = quote(self.device_key, safe="")
        title = quote(message.title, safe="")
        body = quote(message.body, safe="")
        return f"{self.server_url}/{key}/{title}/{body}"

    def _build_params(self, message: NotificationMessage) -> dict[str, str]:
        params: dict[str, str] = {}
        sound = message.sound or self.sound
        group = message.group or self.group
        if sound:
            params["sound"] = sound
        if group:
            params["group"] = group
        if message.url:
            params["url"] = message.url
        return params

    def _extract_api_error(self, response: httpx.Response) -> str | None:
        try:
            payload = response.json()
        except ValueError:
            return None
        code = payload.get("code")
        if code is None or code in (0, 200):
            return None
        message = payload.get("message") or payload.get("error") or payload
        return f"Bark API returned code {code}: {message}"
