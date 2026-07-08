"""
CROO Data & Verification Agent — Edge Case & Resilience Test Suite
==================================================================
Framework  : pytest + FastAPI TestClient + unittest.mock
Coverage   : /verify, /cap/hire, /cap/settle + _fetch_url_content
Focus      : Boundary conditions, protocol abuse, memory-safety limits,
             double-spending, rate limiting, and network failure modes.

Run all tests:
    pytest test_edge_cases.py -v

Run a specific class:
    pytest test_edge_cases.py::TestVerifyEdgeCases -v

Run with short-circuit on first failure:
    pytest test_edge_cases.py -v -x
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from main import (
    SETTLEMENT_ADDRESS,
    FEE_UNITS_PER_CALL,
    MAX_WORDS_LIMIT,
    _active_sessions,
    _seen_tx_hashes,
    app,
)

# ── Shared test client (raise_server_exceptions=False so we assert on HTTP codes)
client = TestClient(app, raise_server_exceptions=False)

# ── Shared helpers ──────────────────────────────────────────────────────────────

VALID_HIRE_PAYLOAD: dict = {
    "caller_agent_id": "edge-test-agent-001",
    "task": "verify",
    "payment_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "max_fee_units": 500,
    "callback_url": None,
}

VALID_TEXT = (
    "According to a peer-reviewed study published in the journal Nature, "
    "researchers at Harvard University have found strong evidence that "
    "regular moderate exercise significantly reduces the risk of "
    "cardiovascular disease across all age groups studied."
)


def _do_hire(payload: dict = None) -> dict:
    """Helper: create a fresh CAP session and return the JSON response."""
    resp = client.post("/cap/hire", json=payload or VALID_HIRE_PAYLOAD)
    assert resp.status_code == 200, f"Hire failed: {resp.text}"
    return resp.json()


def _settle(session_id: str, tx_hash: str = "0xdeadbeef1234567890") -> httpx.Response:
    """Helper: submit a settlement for the given session."""
    return client.post(
        "/cap/settle",
        json={
            "session_id": session_id,
            "tx_hash": tx_hash,
            "from_address": "0xCa11eRaddReSs0000000000000000000000000001",
            "to_address": SETTLEMENT_ADDRESS,
            "fee_units": FEE_UNITS_PER_CALL,
        },
    )


# ══════════════════════════════════════════════════════════════════════════════
# Group 1: /verify — Text content edge cases
# ══════════════════════════════════════════════════════════════════════════════

class TestVerifyEdgeCases:
    """Hammer the /verify endpoint with pathological text inputs."""

    def test_empty_string_returns_422(self):
        """An empty string must be rejected before the NLP pipeline is touched."""
        resp = client.post("/verify", json={"text": ""})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_whitespace_only_returns_422(self):
        """A string of only spaces/newlines carries zero information."""
        resp = client.post("/verify", json={"text": "     \n\t   "})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_four_char_text_returns_422(self):
        """Fewer than 5 chars is below the minimum content guard."""
        resp = client.post("/verify", json={"text": "Hi!!"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_five_char_text_is_accepted(self):
        """At the boundary (5 chars), the request must succeed."""
        resp = client.post("/verify", json={"text": "Hello"})
        assert resp.status_code == status.HTTP_200_OK, resp.text
        data = resp.json()
        assert "overall_credibility_score" in data
        assert 0.0 <= data["overall_credibility_score"] <= 1.0

    def test_no_text_no_url_returns_400(self):
        """Neither field: must 400, not 500."""
        resp = client.post("/verify", json={"caller_agent_id": "agent-x"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text

    def test_gibberish_text_does_not_crash(self):
        """
        Random-looking characters may trip langdetect.
        The server must NOT crash — either 200 or 422 is acceptable.
        """
        resp = client.post(
            "/verify",
            json={"text": "xkzzpq vlrrt mnbvcxz asdfghjkl qwertyuiop 1234567890 !@#$"},
        )
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ), f"Unexpected status {resp.status_code}: {resp.text}"

    def test_arabic_text_does_not_crash(self):
        """Arabic or CJK text must be processed without crashing."""
        arabic = (
            "وفقاً لدراسة منشورة في مجلة نيتشر، وجد الباحثون في جامعة هارفارد "
            "دليلاً قوياً على أن ممارسة التمارين الرياضية المعتدلة بانتظام تقلل "
            "بشكل كبير من خطر الإصابة بأمراض القلب والأوعية الدموية."
        )
        resp = client.post("/verify", json={"text": arabic})
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ), f"Arabic text caused unexpected {resp.status_code}: {resp.text}"

    def test_oversized_text_returns_413_or_422(self):
        """
        A text exceeding MAX_WORDS_LIMIT words must be rejected.
        Pydantic catches it at 422; the endpoint guard emits 413.
        Either is acceptable; a 500 is never acceptable.
        """
        oversized = ("word " * (MAX_WORDS_LIMIT + 500)).strip()
        resp = client.post("/verify", json={"text": oversized})
        assert resp.status_code in (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ), f"Oversized payload got unexpected {resp.status_code}: {resp.text}"

    def test_valid_text_returns_full_schema(self):
        """Smoke-test the happy path and validate the complete response schema."""
        resp = client.post("/verify", json={"text": VALID_TEXT})
        assert resp.status_code == status.HTTP_200_OK, resp.text
        data = resp.json()
        required_keys = {
            "verification_id", "timestamp", "source_type",
            "overall_credibility_score", "label", "confidence",
            "dimensions", "flags", "language", "word_count",
            "reading_ease", "summary", "cap_billed",
        }
        assert required_keys.issubset(data.keys()), (
            f"Missing keys: {required_keys - data.keys()}"
        )
        assert len(data["dimensions"]) == 7, (
            f"Expected 7 dimensions (including Psych Manipulation), "
            f"got {len(data['dimensions'])}"
        )
        assert data["source_type"] == "text"
        assert data["cap_billed"] is False

    def test_single_repeated_character_blob(self):
        """A blob of a single character repeated should not crash the NLP pipeline."""
        resp = client.post("/verify", json={"text": "a" * 300})
        assert resp.status_code in (
            status.HTTP_200_OK,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ), f"Repeated-char blob caused {resp.status_code}: {resp.text}"


# ══════════════════════════════════════════════════════════════════════════════
# Group 2: /verify — URL edge cases (with mocked network)
# ══════════════════════════════════════════════════════════════════════════════

class TestVerifyURLEdgeCases:
    """URL-mode tests. Network calls are mocked to keep tests fast and hermetic."""

    def test_malformed_scheme_returns_422(self):
        """'htt://' is not a valid scheme; Pydantic must reject it at 422."""
        resp = client.post("/verify", json={"url": "htt://bad-url.example.com"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_ftp_scheme_returns_422(self):
        resp = client.post("/verify", json={"url": "ftp://files.example.com/data.txt"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_url_missing_hostname_returns_422(self):
        resp = client.post("/verify", json={"url": "https://"})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_url_fetch_timeout_returns_408(self):
        """Simulate a connection timeout — must surface as 408, not 500."""
        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = httpx.TimeoutException("timed out")

            resp = client.post(
                "/verify",
                json={"url": "https://very-slow-site.example.com/article"},
            )
        assert resp.status_code == status.HTTP_408_REQUEST_TIMEOUT, (
            f"Expected 408 on timeout, got {resp.status_code}: {resp.text}"
        )

    def test_url_fetch_connection_error_returns_502(self):
        """DNS failure or connection refused must surface as 502."""
        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_client.get.side_effect = httpx.ConnectError("connection refused")

            resp = client.post(
                "/verify",
                json={"url": "https://non-existent-domain-xyz.example.com/"},
            )
        assert resp.status_code == status.HTTP_502_BAD_GATEWAY, (
            f"Expected 502 on connection error, got {resp.status_code}: {resp.text}"
        )

    def test_url_fetch_403_returns_422(self):
        """Remote 403 must produce 422, not an unhandled crash."""
        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 403
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = client.post(
                "/verify",
                json={"url": "https://paywalled-site.example.com/article"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Expected 422 on 403, got {resp.status_code}: {resp.text}"
        )
        assert "403" in resp.text or "Forbidden" in resp.text

    def test_url_fetch_404_returns_422(self):
        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = client.post(
                "/verify",
                json={"url": "https://example.com/page-does-not-exist"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "404" in resp.text or "Not Found" in resp.text

    def test_url_empty_page_returns_422(self):
        """A valid HTTP 200 but empty body must be caught gracefully."""
        with patch("main.httpx.AsyncClient") as mock_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.text = "<html><body></body></html>"
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = client.post(
                "/verify",
                json={"url": "https://empty-page.example.com/"},
            )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Expected 422 for empty page, got {resp.status_code}: {resp.text}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Group 3: /cap/hire — Protocol abuse
# ══════════════════════════════════════════════════════════════════════════════

class TestCapHireEdgeCases:
    """Stress the hiring endpoint against malformed and abusive payloads."""

    def test_zero_fee_units_returns_422(self):
        """
        Pydantic validator catches zero fee before the endpoint runs.
        Must return 422, not 402.
        """
        payload = {**VALID_HIRE_PAYLOAD, "max_fee_units": 0}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
            f"Zero fee should be 422, got {resp.status_code}: {resp.text}"
        )

    def test_negative_fee_units_returns_422(self):
        """Negative fee units violate the ge=0 constraint."""
        payload = {**VALID_HIRE_PAYLOAD, "max_fee_units": -50}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_insufficient_positive_fee_units_returns_402(self):
        """A fee of 1 unit (valid, non-zero) but below FEE_UNITS_PER_CALL must be 402."""
        if FEE_UNITS_PER_CALL <= 1:
            pytest.skip("FEE_UNITS_PER_CALL is 1; can't test insufficient positive fee.")
        payload = {**VALID_HIRE_PAYLOAD, "max_fee_units": 1}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, (
            f"Insufficient fee should be 402, got {resp.status_code}: {resp.text}"
        )

    def test_unknown_task_returns_400(self):
        """Requesting a task other than 'verify' must 400."""
        payload = {**VALID_HIRE_PAYLOAD, "task": "hack_the_planet"}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text
        assert "verify" in resp.text.lower()

    def test_blank_caller_agent_id_returns_422(self):
        """A blank caller_agent_id must be rejected at the Pydantic layer."""
        payload = {**VALID_HIRE_PAYLOAD, "caller_agent_id": "   "}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_missing_payment_token_returns_422(self):
        """Omitting payment_token must produce a validation error."""
        payload = {k: v for k, v in VALID_HIRE_PAYLOAD.items() if k != "payment_token"}
        resp = client.post("/cap/hire", json=payload)
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_valid_hire_creates_session(self):
        """Sanity check: a fully valid hire must return 200 with a session_id."""
        resp = client.post("/cap/hire", json=VALID_HIRE_PAYLOAD)
        assert resp.status_code == status.HTTP_200_OK, resp.text
        data = resp.json()
        assert data["session_id"].startswith("cap-sess-")
        assert data["status"] == "active"
        assert data["fee_units"] == FEE_UNITS_PER_CALL

    def test_empty_body_returns_422(self):
        resp = client.post("/cap/hire", json={})
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text

    def test_non_json_body_returns_422(self):
        resp = client.post(
            "/cap/hire",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, resp.text


# ══════════════════════════════════════════════════════════════════════════════
# Group 4: /cap/settle — Double-spend & protocol abuse
# ══════════════════════════════════════════════════════════════════════════════

class TestCapSettleEdgeCases:
    """Verify the settlement endpoint is bulletproof against replay and abuse."""

    def setup_method(self):
        """Create a fresh session for each test to guarantee isolation."""
        self.session_data = _do_hire()
        self.session_id = self.session_data["session_id"]
        # Use a unique tx hash per test instance to avoid cross-test collisions
        self.tx_hash = f"0xunique{id(self):016x}"

    def test_fake_session_id_returns_404(self):
        """A session ID that was never created must 404."""
        resp = _settle("cap-sess-000000000000000000000000000000000000000000")
        assert resp.status_code == status.HTTP_404_NOT_FOUND, resp.text

    def test_malformed_session_id_format_returns_400(self):
        """A session_id that doesn't start with 'cap-sess-' must 400."""
        resp = _settle("not-a-valid-session-id")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text
        assert "malformed" in resp.text.lower() or "cap-sess-" in resp.text.lower()

    def test_double_spend_same_session_returns_409(self):
        """
        Settling an already-settled session must be rejected with 409.
        This guards against double-spending regardless of the tx_hash.
        """
        resp1 = _settle(self.session_id, tx_hash=self.tx_hash)
        assert resp1.status_code == status.HTTP_200_OK, (
            f"First settle failed: {resp1.text}"
        )
        resp2 = _settle(self.session_id, tx_hash=self.tx_hash + "b")
        assert resp2.status_code == status.HTTP_409_CONFLICT, (
            f"Double-spend should be 409, got {resp2.status_code}: {resp2.text}"
        )
        assert "settled" in resp2.text.lower() or "double" in resp2.text.lower()

    def test_duplicate_tx_hash_different_session_returns_409(self):
        """
        Re-using the same on-chain tx_hash for a different session is a
        double-spend attack and must be rejected with 409.
        """
        shared_tx_hash = f"0xsharedTx{id(self):016x}"

        session_a = _do_hire()
        resp1 = _settle(session_a["session_id"], tx_hash=shared_tx_hash)
        assert resp1.status_code == status.HTTP_200_OK, f"Session A settle failed: {resp1.text}"

        session_b = _do_hire()
        resp2 = _settle(session_b["session_id"], tx_hash=shared_tx_hash)
        assert resp2.status_code == status.HTTP_409_CONFLICT, (
            f"Duplicate tx_hash should be 409, got {resp2.status_code}: {resp2.text}"
        )

    def test_wrong_to_address_returns_400(self):
        """Settling to a different wallet address must 400."""
        resp = client.post(
            "/cap/settle",
            json={
                "session_id": self.session_id,
                "tx_hash": self.tx_hash,
                "from_address": "0xCallerWalletAddress0000000000000000000001",
                "to_address": "0xWrongAddressDeadBeef00000000000000000002",
                "fee_units": FEE_UNITS_PER_CALL,
            },
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST, resp.text

    def test_insufficient_fee_units_at_settle_returns_402(self):
        """Settling with less than the agreed fee must 402."""
        if FEE_UNITS_PER_CALL <= 1:
            pytest.skip("FEE_UNITS_PER_CALL is 1; can't send less.")
        resp = client.post(
            "/cap/settle",
            json={
                "session_id": self.session_id,
                "tx_hash": self.tx_hash,
                "from_address": "0xCallerWalletAddress0000000000000000000001",
                "to_address": SETTLEMENT_ADDRESS,
                "fee_units": FEE_UNITS_PER_CALL - 1,
            },
        )
        assert resp.status_code == status.HTTP_402_PAYMENT_REQUIRED, resp.text

    def test_expired_session_returns_410(self):
        """Manually backdate a session's expiry and confirm it returns 410."""
        _active_sessions[self.session_id]["expires_at"] = time.time() - 1.0
        resp = _settle(self.session_id, tx_hash=self.tx_hash)
        assert resp.status_code == status.HTTP_410_GONE, (
            f"Expired session should be 410, got {resp.status_code}: {resp.text}"
        )
        assert "expired" in resp.text.lower()

    def test_valid_settlement_returns_full_schema(self):
        """Sanity check: a valid settlement must return a complete receipt."""
        resp = _settle(self.session_id, tx_hash=self.tx_hash)
        assert resp.status_code == status.HTTP_200_OK, resp.text
        data = resp.json()
        required_keys = {
            "settlement_id", "session_id", "status",
            "confirmed_block", "timestamp", "receipt",
        }
        assert required_keys.issubset(data.keys()), (
            f"Missing keys: {required_keys - data.keys()}"
        )
        assert data["status"] == "settled"
        assert data["session_id"] == self.session_id
        assert isinstance(data["confirmed_block"], int)


# ══════════════════════════════════════════════════════════════════════════════
# Group 5: Rate limit simulation
# ══════════════════════════════════════════════════════════════════════════════

class TestRateLimiting:
    """
    Simulate hitting the rate limits.
    slowapi tracks state per IP. TestClient uses 127.0.0.1 by default.
    """

    def test_rate_limit_triggers_on_31st_verify_request(self):
        """
        Fire 31 rapid requests against /verify.
        At least one must receive HTTP 429 Too Many Requests.
        """
        results: list[int] = []
        payload = {"text": VALID_TEXT}

        for _ in range(31):
            resp = client.post("/verify", json=payload)
            results.append(resp.status_code)
            if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        assert status.HTTP_429_TOO_MANY_REQUESTS in set(results), (
            f"Expected at least one 429 in 31 rapid /verify requests. "
            f"Got only: {set(results)}. "
            "The rate limiter may not be active in test mode."
        )

    def test_hire_rate_limit_triggers_on_61st_request(self):
        """
        /cap/hire is capped at 60/minute. Verify the limiter activates.
        """
        results: list[int] = []

        for _ in range(61):
            resp = client.post("/cap/hire", json=VALID_HIRE_PAYLOAD)
            results.append(resp.status_code)
            if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        assert status.HTTP_429_TOO_MANY_REQUESTS in set(results), (
            f"Expected at least one 429 in 61 rapid /cap/hire requests. "
            f"Got statuses: {set(results)}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# Group 6: /health liveness probe
# ══════════════════════════════════════════════════════════════════════════════

class TestHealthProbe:
    """The /health endpoint must always return 200 regardless of external state."""

    def test_health_check_returns_200(self):
        resp = client.get("/health")
        assert resp.status_code == status.HTTP_200_OK, resp.text

    def test_health_check_has_required_fields(self):
        resp = client.get("/health")
        data = resp.json()
        assert "status" in data
        assert "agent_id" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"


# ══════════════════════════════════════════════════════════════════════════════
# Group 7: Full lifecycle — hire → verify → double-settle
# ══════════════════════════════════════════════════════════════════════════════

class TestFullLifecycleEdgeCases:
    """End-to-end flow tests that simulate realistic A2A interactions then abuse."""

    def test_full_lifecycle_with_double_settle_attempt(self):
        """
        Complete the full CAP flow:
          1. Hire       -> creates a valid session
          2. Verify     -> uses the session (cap_billed=True)
          3. Settle #1  -> succeeds
          4. Settle #2  -> must be rejected with 409
        """
        hire_resp = client.post("/cap/hire", json=VALID_HIRE_PAYLOAD)
        assert hire_resp.status_code == 200, hire_resp.text
        session_id = hire_resp.json()["session_id"]

        verify_resp = client.post(
            "/verify",
            json={"text": VALID_TEXT, "session_id": session_id},
        )
        assert verify_resp.status_code == 200, verify_resp.text
        assert verify_resp.json()["cap_billed"] is True

        unique_tx = f"0xlifecycle{id(self):016x}a"

        settle1 = _settle(session_id, tx_hash=unique_tx)
        assert settle1.status_code == 200, f"First settle failed: {settle1.text}"

        settle2 = _settle(session_id, tx_hash=unique_tx + "b")
        assert settle2.status_code == status.HTTP_409_CONFLICT, (
            f"Double-spend should return 409, got {settle2.status_code}: {settle2.text}"
        )

    def test_verify_with_fake_session_still_processes_but_unbilled(self):
        """
        Providing a non-existent session_id must NOT crash the /verify endpoint.
        The request is processed as unbilled (cap_billed=False).
        """
        resp = client.post(
            "/verify",
            json={
                "text": VALID_TEXT,
                "session_id": "cap-sess-this-id-does-not-exist-000",
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["cap_billed"] is False

    def test_verify_after_settled_session_does_not_crash(self):
        """
        After a session is settled, /verify with that session_id should
        still complete without crashing (server resilience).
        """
        session = _do_hire()
        sid = session["session_id"]
        tx = f"0xrevfy{id(self):016x}"

        r1 = client.post("/verify", json={"text": VALID_TEXT, "session_id": sid})
        assert r1.status_code == 200

        s = _settle(sid, tx_hash=tx)
        assert s.status_code == 200, s.text

        r2 = client.post("/verify", json={"text": VALID_TEXT, "session_id": sid})
        assert r2.status_code == 200, (
            f"Server crashed after settled session: {r2.text}"
        )
