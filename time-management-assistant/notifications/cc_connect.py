import subprocess

from notifications.base import NotificationMessage, NotificationResult


class CCConnectNotifier:
    channel = "wechat_work"

    def __init__(
        self,
        *,
        project: str = "my-project",
        command: str = "cc-connect",
        timeout_seconds: float = 30.0,
    ) -> None:
        self.project = project
        self.command = command
        self.timeout_seconds = timeout_seconds

    def send(self, message: NotificationMessage) -> NotificationResult:
        if message.channel != self.channel:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=f"cc-connect notifier cannot send channel: {message.channel}",
            )
        if not self.project:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message="CC_CONNECT_PROJECT is required.",
            )

        text = self._format_message(message)
        try:
            result = subprocess.run(
                [self.command, "send", "-p", self.project, "-m", text],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except Exception as exc:
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=str(exc),
            )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        if result.returncode != 0:
            detail = stderr or stdout or f"exit code {result.returncode}"
            return NotificationResult(
                success=False,
                channel=self.channel,
                error_message=f"cc-connect send failed: {detail}",
                status_code=result.returncode,
                response_body=stdout or stderr or None,
            )

        return NotificationResult(
            success=True,
            channel=self.channel,
            status_code=0,
            response_body=stdout or None,
        )

    def _format_message(self, message: NotificationMessage) -> str:
        body = message.body.strip()
        title = message.title.strip()
        if not title:
            return body
        if not body:
            return title
        return f"{title}\n\n{body}"
