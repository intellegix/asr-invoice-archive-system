"""
Shared auth constants for test modules.
Centralizes Bearer tokens, CSRF headers, and cookie values
to avoid duplication across test files.
"""

AUTH_HEADERS = {"Authorization": "Bearer test-key"}
CSRF_TOKEN = "test-csrf-token"
WRITE_HEADERS = {
    "Authorization": "Bearer test-key",
    "x-csrf-token": CSRF_TOKEN,
}
CSRF_COOKIES = {"csrf_token": CSRF_TOKEN}
