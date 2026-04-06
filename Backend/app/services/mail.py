from dataclasses import dataclass
import importlib
from typing import Final

from app.core.config import settings


GRAPH_SCOPE: Final[list[str]] = ["https://graph.microsoft.com/.default"]


@dataclass(slots=True)
class MailSendResult:
    success: bool
    message: str


def _is_mail_service_configured() -> bool:
    return bool(
        settings.mail_client_id
        and settings.mail_client_secret
        and settings.mail_tenant_id
        and settings.mail_sender_user
    )


def send_submission_mail(*, recipient_email: str, subject: str, body_text: str) -> MailSendResult:
    recipient = recipient_email.strip()
    if not recipient:
        return MailSendResult(success=False, message="Recipient email is missing.")

    if not _is_mail_service_configured():
        return MailSendResult(
            success=False,
            message=(
                "Mail service is not configured. Set CLIENT_ID, CLIENT_SECRET, TENANT_ID, "
                "and MAIL_SENDER_USER environment values."
            ),
        )

    try:
        requests_module = importlib.import_module("requests")
    except ImportError:
        return MailSendResult(
            success=False,
            message="requests package is not installed. Install backend dependencies before sending mail.",
        )

    authority = f"https://login.microsoftonline.com/{settings.mail_tenant_id}"
    try:
        msal_module = importlib.import_module("msal")
        confidential_client_cls = getattr(msal_module, "ConfidentialClientApplication")
    except (ImportError, AttributeError):
        return MailSendResult(
            success=False,
            message="msal package is not installed. Install backend dependencies before sending mail.",
        )

    app = confidential_client_cls(
        str(settings.mail_client_id),
        authority=authority,
        client_credential=str(settings.mail_client_secret),
    )

    token_payload = app.acquire_token_for_client(scopes=GRAPH_SCOPE)
    access_token = token_payload.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        detail = (
            token_payload.get("error_description")
            or token_payload.get("error")
            or "Unable to acquire Microsoft Graph access token."
        )
        return MailSendResult(success=False, message=f"Token request failed: {detail}")

    request_payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body_text,
            },
            "toRecipients": [
                {"emailAddress": {"address": recipient}},
            ],
        }
    }

    try:
        response = requests_module.post(
            f"https://graph.microsoft.com/v1.0/users/{settings.mail_sender_user}/sendMail",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=request_payload,
            timeout=settings.mail_request_timeout_seconds,
        )
    except requests_module.RequestException as exc:
        return MailSendResult(success=False, message=f"Mail request failed: {exc}")

    if response.status_code not in (200, 202):
        detail = response.text.strip()
        if len(detail) > 500:
            detail = f"{detail[:500]}..."
        return MailSendResult(
            success=False,
            message=f"Graph sendMail failed ({response.status_code}): {detail or 'No response body.'}",
        )

    return MailSendResult(success=True, message="Mail sent successfully.")