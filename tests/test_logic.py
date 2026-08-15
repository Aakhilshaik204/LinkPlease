"""
tests/test_logic.py
Unit tests for core logic components (Cryptography & Text Matching).
Run with: pytest
"""
import pytest
import hashlib
import hmac

# We can import directly from our app modules
from app.routes.webhook import _verify_signature

def test_verify_signature_valid():
    """Test that HMAC-SHA256 verification succeeds with a correct signature."""
    secret_key = "test_secret_key"
    payload = b'{"event_id": "123", "text": "hello"}'
    
    # Generate the valid signature manually
    mac = hmac.new(secret_key.encode(), payload, hashlib.sha256).hexdigest()
    sig_header = f"sha256={mac}"
    
    # Temporarily override the config key for testing
    import app.config
    original_key = app.config.PSEUDOGRAM_API_KEY
    app.config.PSEUDOGRAM_API_KEY = secret_key
    
    try:
        assert _verify_signature(payload, sig_header) == True
    finally:
        app.config.PSEUDOGRAM_API_KEY = original_key


def test_verify_signature_invalid():
    """Test that a forged or mismatched signature is rejected."""
    secret_key = "test_secret_key"
    payload = b'{"event_id": "123", "text": "hello"}'
    forged_sig_header = "sha256=abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    
    import app.config
    original_key = app.config.PSEUDOGRAM_API_KEY
    app.config.PSEUDOGRAM_API_KEY = secret_key
    
    try:
        assert _verify_signature(payload, forged_sig_header) == False
    finally:
        app.config.PSEUDOGRAM_API_KEY = original_key


def test_verify_signature_missing_prefix():
    """Test rejection of headers that lack the 'sha256=' prefix."""
    assert _verify_signature(b'{}', "justsomerandomhash") == False
