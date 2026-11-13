"""Set up a fresh platform for the eval gate: an owner, a member token and, when the repo has
one, the Gemini key the regression report uses. Prints the settings evalctl reads, for
$GITHUB_ENV."""

import os
import secrets

import httpx

URL = os.environ.get("AGENT_EVAL_URL", "http://127.0.0.1:8000")


def main() -> None:
    password = secrets.token_urlsafe(24)
    with httpx.Client(base_url=URL, timeout=30) as client:
        client.post(
            "/api/v1/auth/setup",
            json={"email": "ci@example.com", "password": password, "workspace_name": "CI"},
        ).raise_for_status()
        login = client.post(
            "/api/v1/auth/login", json={"email": "ci@example.com", "password": password}
        )
        login.raise_for_status()
        headers = {"x-csrf-token": login.json()["csrf_token"]}
        token = client.post(
            "/api/v1/api-tokens", json={"name": "eval-gate", "role": "member"}, headers=headers
        )
        token.raise_for_status()
        key = os.environ.get("GEMINI_API_KEY")
        if key:
            client.post(
                "/api/v1/provider-credentials",
                json={"provider": "gemini", "label": "ci", "api_key": key},
                headers=headers,
            ).raise_for_status()
    print(f"AGENT_EVAL_URL={URL}")
    print(f"AGENT_EVAL_TOKEN={token.json()['token']}")


if __name__ == "__main__":
    main()
