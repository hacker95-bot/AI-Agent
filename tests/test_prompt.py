import hashlib
import hmac
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.wa import verify_signature


def test_verify_signature():
    secret = "top"
    payload = b"hello"
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_signature(sig, payload, secret)
