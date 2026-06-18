"""
Tests for the transactional email abstraction (no DB, no network).
Run: pytest tests/ -v
"""
import pytest

from app.config import settings
from app.services import email as email_mod
from app.services.email import send_email, clear_outbox, outbox, EmailError, get_backend, ConsoleBackend
from app.services.email.templates import report_ready, verify_email, reset_password


@pytest.fixture(autouse=True)
def _clean_outbox():
    clear_outbox()
    original = settings.EMAIL_BACKEND
    settings.EMAIL_BACKEND = "console"
    yield
    settings.EMAIL_BACKEND = original
    clear_outbox()


def test_default_backend_is_console():
    assert isinstance(get_backend(), ConsoleBackend)


def test_send_email_captures_to_outbox():
    msg = send_email(to="m@x.org", subject="Hi", html="<p>hi</p>")
    assert len(outbox) == 1
    assert outbox[0].to == "m@x.org"
    assert outbox[0].subject == "Hi"
    assert msg.from_addr == settings.EMAIL_FROM


def test_send_email_custom_from():
    send_email(to="m@x.org", subject="Hi", html="<p>hi</p>", from_addr="custom@x.org")
    assert outbox[0].from_addr == "custom@x.org"


def test_clear_outbox():
    send_email(to="m@x.org", subject="Hi", html="<p>hi</p>")
    clear_outbox()
    assert outbox == []


def test_unknown_backend_raises():
    settings.EMAIL_BACKEND = "carrier-pigeon"
    with pytest.raises(EmailError):
        send_email(to="m@x.org", subject="Hi", html="<p>hi</p>")


def test_sendgrid_backend_refuses_without_api_key():
    settings.EMAIL_BACKEND = "sendgrid"
    settings.SENDGRID_API_KEY = ""
    with pytest.raises(EmailError):
        send_email(to="m@x.org", subject="Hi", html="<p>hi</p>")
    assert outbox == []  # nothing captured, nothing sent


# ── templates ─────────────────────────────────────────────────────────────────

def test_report_ready_template_includes_link():
    subject, html = report_ready("https://app.bhis.io/report/tok123")
    assert "results" in subject.lower()
    assert "https://app.bhis.io/report/tok123" in html

def test_verify_and_reset_templates():
    s1, h1 = verify_email("https://x/verify?t=1")
    s2, h2 = reset_password("https://x/reset?t=1")
    assert "https://x/verify?t=1" in h1
    assert "https://x/reset?t=1" in h2
    assert s1 and s2
