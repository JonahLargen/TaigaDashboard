import requests
import base64
import json
import time


class TaigaClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.auth_token = None
        self.refresh_token = None

    def is_authenticated(self):
        if self.auth_token is None:
            return False
        if self.is_token_expired(self.auth_token):
            return False

        return True

    def authenticate(self):
        """Authenticate the user and store the session cookie."""
        if self.refresh_token is not None and not self.is_token_expired(self.refresh_token):
            url = f"{self.base_url}/api/v1/auth/refresh"
            json_payload = {"refresh": self.refresh_token}
            headers = {"Content-Type": "application/json"}
            response = self.session.post(url, json=json_payload, headers=headers)
            response.raise_for_status()
            data = response.json()
        else:
            url = f"{self.base_url}/api/v1/auth"
            json_payload = {
                "username": self.username,
                "password": self.password,
                "type": "normal",
            }
            headers = {"Content-Type": "application/json"}
            response = self.session.post(url, json=json_payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        self.auth_token = data.get("auth_token")
        self.refresh_token = data.get("refresh")

        if not self.auth_token or not self.refresh_token:
            raise ValueError("Authentication failed. Please check your credentials.")

        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})

    def is_token_expired(self, token):
        """Check if a token (JWT) is expired. Supports JWT tokens only."""
        try:
            # JWTs have 3 parts separated by '.', get the payload
            parts = token.split(".")
            if len(parts) != 3:
                return False  # Not a JWT, can't check
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)  # pad base64
            payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode("utf-8"))
            exp = payload.get("exp")
            if exp is None:
                return False  # No exp claim, assume not expired
            return exp < int(time.time())
        except Exception:
            return False

    def ensure_authenticated(self):
        """Ensure the user is authenticated, re-authenticate if necessary."""
        if not self.is_authenticated():
            self.authenticate()