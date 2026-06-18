"""
Transactional email abstraction.

A small, pluggable backend so the app code calls one ``send_email(...)`` and the
delivery mechanism is chosen by config:

  - ``console`` (default): captures messages in an in-process ``outbox`` and logs
    them. Used in dev and tests — nothing leaves the machine.
  - ``sendgrid``: posts to the SendGrid v3 REST API via httpx (no extra
    dependency). Inert unless ``SENDGRID_API_KEY`` is set, so it cannot send by
    accident.

Templates live in app.services.email.templates and return (subject, html).
"""
import logging
from dataclasses import dataclass
from typing import List

import httpx

from app.config import settings

logger = logging.getLogger("bhis.email")


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str
    from_addr: str


# In-process capture for the console backend (and test assertions).
outbox: List[EmailMessage] = []


class EmailError(RuntimeError):
    """Raised when a backend is selected but not usable (e.g. missing API key)."""


class ConsoleBackend:
    def send(self, message: EmailMessage) -> None:
        outbox.append(message)
        logger.info("EMAIL (console) to=%s subject=%s", message.to, message.subject)


class SendGridBackend:
    API_URL = "https://api.sendgrid.com/v3/mail/send"

    def send(self, message: EmailMessage) -> None:
        if not settings.SENDGRID_API_KEY:
            raise EmailError(
                "EMAIL_BACKEND=sendgrid but SENDGRID_API_KEY is not set; refusing to send."
            )
        payload = {
            "personalizations": [{"to": [{"email": message.to}]}],
            "from": {"email": message.from_addr},
            "subject": message.subject,
            "content": [{"type": "text/html", "value": message.html}],
        }
        resp = httpx.post(
            self.API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            timeout=10.0,
        )
        if resp.status_code >= 400:
            raise EmailError(f"SendGrid send failed: {resp.status_code} {resp.text}")


_BACKENDS = {"console": ConsoleBackend, "sendgrid": SendGridBackend}


def get_backend():
    backend_cls = _BACKENDS.get(settings.EMAIL_BACKEND)
    if backend_cls is None:
        raise EmailError(f"Unknown EMAIL_BACKEND: {settings.EMAIL_BACKEND!r}")
    return backend_cls()


def send_email(to: str, subject: str, html: str, from_addr: str = None) -> EmailMessage:
    """Send a transactional email via the configured backend. Returns the message."""
    message = EmailMessage(
        to=to,
        subject=subject,
        html=html,
        from_addr=from_addr or settings.EMAIL_FROM,
    )
    get_backend().send(message)
    return message


def clear_outbox() -> None:
    outbox.clear()
