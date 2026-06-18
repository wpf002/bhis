"""
HTML templates for transactional emails. Each returns (subject, html).

Kept deliberately plain — no external template engine. The report-delivery
template is the only one wired today; verification/reset templates are provided
so the auth-email phase can drop straight in.
"""
from typing import Tuple

_WRAP = (
    '<div style="font-family:system-ui,sans-serif;max-width:520px;margin:0 auto;'
    'color:#1a1a1a;line-height:1.5">{body}</div>'
)


def _button(url: str, label: str) -> str:
    return (
        f'<a href="{url}" style="display:inline-block;padding:12px 20px;'
        f'background:#2b6cb0;color:#fff;border-radius:6px;text-decoration:none">{label}</a>'
    )


def report_ready(report_url: str) -> Tuple[str, str]:
    body = (
        "<h2>Your BHIS results are ready</h2>"
        "<p>Thanks for completing the assessment. Your personal report is "
        "available at the private link below. Keep it for yourself — it is tied "
        "to an anonymous token, not your name, and your church cannot see it.</p>"
        f"<p>{_button(report_url, 'View my report')}</p>"
        f'<p style="font-size:13px;color:#666">Or paste this link into your browser:<br>{report_url}</p>'
    )
    return "Your BHIS results are ready", _WRAP.format(body=body)


def verify_email(verify_url: str) -> Tuple[str, str]:
    body = (
        "<h2>Confirm your email</h2>"
        "<p>Confirm your email address to finish setting up your BHIS account.</p>"
        f"<p>{_button(verify_url, 'Confirm email')}</p>"
    )
    return "Confirm your BHIS email", _WRAP.format(body=body)


def reset_password(reset_url: str) -> Tuple[str, str]:
    body = (
        "<h2>Reset your password</h2>"
        "<p>We received a request to reset your BHIS password. If this was you, "
        "use the link below. If not, you can ignore this email.</p>"
        f"<p>{_button(reset_url, 'Reset password')}</p>"
    )
    return "Reset your BHIS password", _WRAP.format(body=body)
