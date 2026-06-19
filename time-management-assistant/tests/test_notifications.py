import httpx

from notifications import BarkNotifier, NotificationMessage
from notifications.factory import CompositeNotifier, DryRunNotifier, create_notifier_from_env


def test_bark_notifier_success() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/test-key/Test title/Test body"
        assert request.url.params["sound"] == "bell"
        assert request.url.params["group"] == "Time Management Assistant"
        return httpx.Response(200, json={"code": 200, "message": "success"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    notifier = BarkNotifier(
        server_url="https://api.day.app",
        device_key="test-key",
        sound="bell",
        group="Time Management Assistant",
        client=client,
    )

    result = notifier.send(
        NotificationMessage(channel="bark", title="Test title", body="Test body")
    )

    assert result.success is True
    assert result.status_code == 200


def test_bark_notifier_http_failure_returns_error() -> None:
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    )
    notifier = BarkNotifier(
        server_url="https://api.day.app",
        device_key="test-key",
        client=client,
    )

    result = notifier.send(
        NotificationMessage(channel="bark", title="Test title", body="Test body")
    )

    assert result.success is False
    assert result.status_code == 500
    assert "status 500" in result.error_message


def test_notification_disabled_uses_dry_run_without_http(monkeypatch) -> None:
    def fail_if_called(*args, **kwargs):
        raise AssertionError("HTTP client should not be created when notifications are disabled.")

    monkeypatch.setattr(httpx, "Client", fail_if_called)
    notifier = create_notifier_from_env({"NOTIFICATION_ENABLED": "false"})

    result = notifier.send(
        NotificationMessage(channel="bark", title="Test title", body="Test body")
    )

    assert isinstance(notifier, DryRunNotifier)
    assert result.success is True


def test_factory_creates_bark_notifier_from_env() -> None:
    notifier = create_notifier_from_env(
        {
            "NOTIFICATION_ENABLED": "true",
            "NOTIFICATION_CHANNELS": "bark",
            "BARK_SERVER_URL": "https://example.test",
            "BARK_DEVICE_KEY": "test-key",
            "BARK_SOUND": "bell",
            "BARK_GROUP": "Time Management Assistant",
        }
    )

    assert isinstance(notifier, CompositeNotifier)
    assert "bark" in notifier.notifiers
