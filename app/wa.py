"""Utilities for interacting with the WhatsApp Cloud API."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import requests

from .config import settings


def verify_signature(signature: str, payload: bytes, secret: str) -> bool:
    """Verify X-Hub-Signature-256 header."""
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(expected, signature)


def send_message(phone_number_id: str, to: str, message: str, token: str | None = None) -> Any:
    """Send a text message via WhatsApp Cloud API."""
    token = token or settings.whatsapp_token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": message},
    }
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    response = requests.post(url, headers=headers, json=data, timeout=5)
    return response.json()
