"""
CROO Data & Verification Agent — Automated Test Suite (v2)
===========================================================
Framework : pytest + FastAPI TestClient
Coverage  : /health, /cap/manifest, /cap/register, /cap/hire,
            /cap/session/{id}, /cap/settle, /verify,
            FactCheckerAgent, SemanticAnalysisAgent,
            Full CAP hire → verify → settle lifecycle
Run       : pytest test_agent.py -v
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from main import (
    SETTLEMENT_ADDRESS,
    FEE_UNITS_PER_CALL,
    CredibilityLabel,
    FactCheckerAgent,
    SemanticAnalysisAgent,
    _fact_checker_agent,
    _semantic_analysis_agent,
    app,
)

# ── Shared test client ──────────────────────────────────────────────────────────
client = TestClient(app, raise_server_exceptions=True)

# ── Shared constants ────────────────────────────────────────────────────────────
HIRE_PAYLOAD = {
    "caller_agent_id": "test-agent-001",
    "task": "verify",
    "payment_token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "max_fee_units": 500,
    "callback_url": None,
}

CREDIBLE_TEXT = (
    "According to a peer-reviewed study published in the journal Nature, "
    "researchers at Harvard University have found strong evidence that regular "
    "moderate exercise significantly reduces the risk of cardiovascular disease. "
    "The study analysed data from over 50,000 participants and was confirmed by "
    "an independent analysis conducted by scientists at the University of Oxford."
)

MISLEADING_TEXT = (
    "SHOCKING!!! Scientists DISCOVERED the ONE CURE they don't want you to know!! "
    "This miracle pill COMPLETELY eliminates ALL disease FOREVER guaranteed!! "
    "They're hiding the truth — EXPLOSIVE cover-up revealed!"
)


@pytest.fixture(scope="module")
def hired_session() -> dict:
    """Module-scoped hired session for lifecycle tests."""
    resp = client.post("/cap/hire", json=HIRE_PAYLOAD)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ══════════════════════════════════════════════════════════════════════════════
# FactCheckerAgent — unit tests
# ══════════════════════════════════════════════════════════════════════════════

class TestFactCheckerAgent:
    """Tests run against the singleton _fact_checker_agent directly."""

    def _run(self, text: str) -> dict:
        return asyncio.run(_fact_checker_agent.run(text))

    def test_returns_dict(self):
        result = self._run(CREDIBLE_TEXT)
        assert isinstance(result, dict)

    def test_has_verified_sources_key(self):
        result = self._run(CREDIBLE_TEXT)
        assert "verified_sources" in result

    def test_verified_sources_is_list(self):
        result = self._run(CREDIBLE_TEXT)
        assert isinstance(result["verified_sources"], list)

    def test_verified_sources_non_empty(self):
        result = self._run(CREDIBLE_TEXT)
        assert len(result["verified_sources"]) >= 2

    def test_verified_sources_are_strings(self):
        result = self._run(CREDIBLE_TEXT)
        for src in result["verified_sources"]:
            assert isinstance(src, str)
            assert src.startswith("http")

    def test_has_source_confidence_score(self):
        result = self._run(CREDIBLE_TEXT)
        assert "source_confidence_score" in result

    def test_source_confidence_score_in_range(self):
        result = self._run(CREDIBLE_TEXT)
        score = result["source_confidence_score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_has_retrieval_method(self):
        result = self._run(CREDIBLE_TEXT)
        assert "retrieval_method" in result
        assert isinstance(result["retrieval_method"], str)

    def test_credible_text_higher_confidence_than_misleading(self):
        cred = self._run(CREDIBLE_TEXT)["source_confidence_score"]
        misl = self._run(MISLEADING_TEXT)["source_confidence_score"]
        assert cred > misl

    def test_deterministic_output_same_text(self):
        """Same input must always yield same sources (deterministic RNG)."""
        r1 = self._run(CREDIBLE_TEXT)
        r2 = self._run(CREDIBLE_TEXT)
        assert r1["verified_sources"] == r2["verified_sources"]
        assert r1["source_confidence_score"] == r2["source_confidence_score"]

    def test_sources_within_allowed_pool(self):
        result = self._run(CREDIBLE_TEXT)
        pool = set(FactCheckerAgent._MOCK_SOURCE_POOL)
        for src in result["verified_sources"]:
            assert src in pool

    def test_short_text_still_returns_valid_result(self):
        result = self._run("hello world")
        assert "verified_sources" in result
        assert 0.0 <= result["source_confidence_score"] <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# SemanticAnalysisAgent — unit tests
# ══════════════════════════════════════════════════════════════════════════════

class TestSemanticAnalysisAgent:
    """Tests run against the singleton _semantic_analysis_agent directly."""

    def _fact_result(self, text: str = CREDIBLE_TEXT) -> dict:
        return asyncio.run(_fact_checker_agent.run(text))

    def _run(self, text: str, nlp_score: float = 0.72, label: str = "LIKELY_CREDIBLE") -> dict:
        fact = self._fact_result(text)
        return asyncio.run(
            _semantic_analysis_agent.run(
                text=text,
                fact_check_result=fact,
                nlp_score=nlp_score,
                label=label,
            )
        )

    def test_returns_dict(self):
        assert isinstance(self._run(CREDIBLE_TEXT), dict)

    def test_has_analytical_summary(self):
        result = self._run(CREDIBLE_TEXT)
        assert "analytical_summary" in result

    def test_analytical_summary_is_non_empty_string(self):
        result = self._run(CREDIBLE_TEXT)
        assert isinstance(result["analytical_summary"], str)
        assert len(result["analytical_summary"]) > 20

    def test_summary_contains_label(self):
        result = self._run(CREDIBLE_TEXT, label="HIGHLY_CREDIBLE")
        # Label readable form appears in the summary
        assert "Highly Credible" in result["analytical_summary"]

    def test_has_composite_confidence(self):
        assert "composite_confidence" in self._run(CREDIBLE_TEXT)

    def test_composite_confidence_in_range(self):
        score = self._run(CREDIBLE_TEXT)["composite_confidence"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_composite_confidence_formula(self):
        """composite = nlp_score * 0.60 + src_conf * 0.40"""
        fact = self._fact_result(CREDIBLE_TEXT)
        result = asyncio.run(
            _semantic_analysis_agent.run(
                text=CREDIBLE_TEXT,
                fact_check_result=fact,
                nlp_score=0.80,
                label="HIGHLY_CREDIBLE",
            )
        )
        expected = round(0.80 * 0.60 + fact["source_confidence_score"] * 0.40, 4)
        assert abs(result["composite_confidence"] - expected) < 1e-6

    def test_has_llm_provider(self):
        assert "llm_provider" in self._run(CREDIBLE_TEXT)

    def test_llm_provider_is_string(self):
        assert isinstance(self._run(CREDIBLE_TEXT)["llm_provider"], str)

    def test_summary_references_source_count(self):
        fact = self._fact_result(CREDIBLE_TEXT)
        result = asyncio.run(
            _semantic_analysis_agent.run(
                text=CREDIBLE_TEXT,
                fact_check_result=fact,
                nlp_score=0.72,
                label="LIKELY_CREDIBLE",
            )
        )
        n = len(fact["verified_sources"])
        assert str(n) in result["analytical_summary"]

    def test_highly_misleading_label_in_summary(self):
        result = self._run(MISLEADING_TEXT, nlp_score=0.15, label="HIGHLY_MISLEADING")
        assert "Highly Misleading" in result["analytical_summary"]


# ══════════════════════════════════════════════════════════════════════════════
# /health
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_returns_200(self):
        assert client.get("/health").status_code == 200

    def test_response_shape(self):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert "agent_id" in body
        assert "timestamp" in body
        assert body["version"] == "1.0.0"

    def test_content_type_is_json(self):
        assert "application/json" in client.get("/health").headers["content-type"]


# ══════════════════════════════════════════════════════════════════════════════
# /cap/manifest
# ══════════════════════════════════════════════════════════════════════════════

class TestCapManifest:
    def test_returns_200(self):
        assert client.get("/cap/manifest").status_code == 200

    def test_required_top_level_fields(self):
        body = client.get("/cap/manifest").json()
        required = {
            "agent_id", "name", "version", "description",
            "capabilities", "input_schema", "output_schema",
            "pricing", "settlement_address", "protocol", "endpoints", "tags",
        }
        assert required.issubset(body.keys())

    def test_protocol_is_cap(self):
        assert client.get("/cap/manifest").json()["protocol"] == "CAP/1.0"

    def test_capabilities_non_empty(self):
        caps = client.get("/cap/manifest").json()["capabilities"]
        assert isinstance(caps, list) and len(caps) > 0

    def test_pricing_fee_matches_constant(self):
        assert client.get("/cap/manifest").json()["pricing"]["fee_units"] == FEE_UNITS_PER_CALL

    def test_settlement_address_matches_constant(self):
        body = client.get("/cap/manifest").json()
        assert body["settlement_address"].lower() == SETTLEMENT_ADDRESS.lower()

    def test_endpoints_map_completeness(self):
        endpoints = client.get("/cap/manifest").json()["endpoints"]
        for key in ("verify", "hire", "settle"):
            assert key in endpoints

    def test_input_schema_has_text_and_url(self):
        props = client.get("/cap/manifest").json()["input_schema"]["properties"]
        assert "text" in props and "url" in props

    def test_output_schema_has_credibility_fields(self):
        props = client.get("/cap/manifest").json()["output_schema"]["properties"]
        assert "overall_credibility_score" in props and "label" in props


# ══════════════════════════════════════════════════════════════════════════════
# /cap/register
# ══════════════════════════════════════════════════════════════════════════════

class TestCapRegister:
    def test_returns_200(self):
        assert client.post("/cap/register").status_code == 200

    def test_status_is_registered(self):
        assert client.post("/cap/register").json()["status"] == "registered"

    def test_listing_id_prefix(self):
        assert client.post("/cap/register").json()["listing_id"].startswith("store-")

    def test_store_url_present(self):
        url = client.post("/cap/register").json()["store_url"]
        assert url.startswith("https://store.croo.ai/agents/")

    def test_manifest_hash_is_sha256(self):
        h = client.post("/cap/register").json()["manifest_hash"]
        assert len(h) == 64


# ══════════════════════════════════════════════════════════════════════════════
# /cap/hire
# ══════════════════════════════════════════════════════════════════════════════

class TestCapHire:
    def test_returns_200(self):
        assert client.post("/cap/hire", json=HIRE_PAYLOAD).status_code == 200

    def test_response_shape(self):
        body = client.post("/cap/hire", json=HIRE_PAYLOAD).json()
        for key in ("session_id", "status", "agent_id", "fee_units",
                    "payment_token", "expires_at", "instructions"):
            assert key in body

    def test_session_id_prefix(self):
        assert client.post("/cap/hire", json=HIRE_PAYLOAD).json()["session_id"].startswith("cap-sess-")

    def test_status_is_active(self):
        assert client.post("/cap/hire", json=HIRE_PAYLOAD).json()["status"] == "active"

    def test_fee_units_matches_constant(self):
        assert client.post("/cap/hire", json=HIRE_PAYLOAD).json()["fee_units"] == FEE_UNITS_PER_CALL

    def test_wrong_task_returns_400(self):
        assert client.post("/cap/hire", json={**HIRE_PAYLOAD, "task": "summarize"}).status_code == 400

    def test_insufficient_fee_returns_402(self):
        assert client.post("/cap/hire", json={**HIRE_PAYLOAD, "max_fee_units": 1}).status_code == 402

    def test_missing_caller_id_returns_422(self):
        bad = {k: v for k, v in HIRE_PAYLOAD.items() if k != "caller_agent_id"}
        assert client.post("/cap/hire", json=bad).status_code == 422

    def test_unique_session_ids(self):
        a = client.post("/cap/hire", json=HIRE_PAYLOAD).json()["session_id"]
        b = client.post("/cap/hire", json=HIRE_PAYLOAD).json()["session_id"]
        assert a != b


# ══════════════════════════════════════════════════════════════════════════════
# /cap/session/{id}
# ══════════════════════════════════════════════════════════════════════════════

class TestCapSession:
    def test_returns_200_for_valid_session(self, hired_session):
        assert client.get(f"/cap/session/{hired_session['session_id']}").status_code == 200

    def test_shows_active_and_unsettled(self, hired_session):
        body = client.get(f"/cap/session/{hired_session['session_id']}").json()
        assert body["status"] == "active"
        assert body["settled"] is False

    def test_unknown_session_returns_404(self):
        assert client.get("/cap/session/cap-sess-nonexistent-xyz").status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# /verify — text input
# ══════════════════════════════════════════════════════════════════════════════

class TestVerifyText:
    def test_returns_200(self):
        assert client.post("/verify", json={"text": CREDIBLE_TEXT}).status_code == 200

    def test_response_schema_complete(self):
        body = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()
        required = {
            "verification_id", "timestamp", "source_type",
            "overall_credibility_score", "label", "confidence",
            "dimensions", "flags", "language", "word_count",
            "reading_ease", "summary", "cap_billed",
        }
        assert required.issubset(body.keys())

    def test_verification_id_prefix(self):
        body = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()
        assert body["verification_id"].startswith("vrfy-")

    def test_source_type_is_text(self):
        assert client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["source_type"] == "text"

    def test_score_in_range(self):
        score = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["overall_credibility_score"]
        assert 0.0 <= score <= 1.0

    def test_confidence_in_range(self):
        conf = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["confidence"]
        assert 0.0 <= conf <= 1.0

    def test_label_is_valid_enum(self):
        label = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["label"]
        assert label in {e.value for e in CredibilityLabel}

    def test_six_dimensions(self):
        dims = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["dimensions"]
        assert len(dims) == 6

    def test_each_dimension_valid(self):
        dims = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["dimensions"]
        for d in dims:
            assert "name" in d and "score" in d and "explanation" in d
            assert 0.0 <= d["score"] <= 1.0

    def test_word_count_positive(self):
        assert client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["word_count"] > 0

    def test_flags_is_list(self):
        assert isinstance(client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["flags"], list)

    def test_cap_billed_false_without_session(self):
        assert client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["cap_billed"] is False

    def test_summary_is_swarm_output(self):
        """Summary must now carry the SemanticAnalysisAgent prefix."""
        summary = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["summary"]
        assert "[SemanticAnalysisAgent]" in summary

    def test_summary_contains_nlp_score(self):
        body = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()
        # The summary embeds the nlp score as a percentage string
        assert "%" in body["summary"]

    def test_summary_references_rag_sources(self):
        summary = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["summary"]
        assert "authoritative source" in summary

    def test_credible_higher_score_than_misleading(self):
        cred = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["overall_credibility_score"]
        misl = client.post("/verify", json={"text": MISLEADING_TEXT}).json()["overall_credibility_score"]
        assert cred > misl

    def test_misleading_has_flags(self):
        flags = client.post("/verify", json={"text": MISLEADING_TEXT}).json()["flags"]
        assert len(flags) > 0

    def test_no_text_no_url_returns_400(self):
        assert client.post("/verify", json={}).status_code == 400

    def test_invalid_url_scheme_returns_422(self):
        assert client.post("/verify", json={"url": "ftp://example.com"}).status_code == 422

    def test_unique_verification_ids(self):
        a = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["verification_id"]
        b = client.post("/verify", json={"text": CREDIBLE_TEXT}).json()["verification_id"]
        assert a != b


# ══════════════════════════════════════════════════════════════════════════════
# /verify — CAP session billing
# ══════════════════════════════════════════════════════════════════════════════

class TestVerifyCapBilling:
    def test_cap_billed_true_with_valid_session(self, hired_session):
        body = client.post("/verify", json={
            "text": CREDIBLE_TEXT,
            "session_id": hired_session["session_id"],
        }).json()
        assert body["cap_billed"] is True

    def test_cap_billed_false_with_unknown_session(self):
        body = client.post("/verify", json={
            "text": CREDIBLE_TEXT,
            "session_id": "cap-sess-bogus-000",
        }).json()
        assert body["cap_billed"] is False

    def test_returns_200_with_valid_session(self, hired_session):
        resp = client.post("/verify", json={
            "text": CREDIBLE_TEXT,
            "session_id": hired_session["session_id"],
        })
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
# /cap/settle
# ══════════════════════════════════════════════════════════════════════════════

class TestCapSettle:
    @pytest.fixture(scope="class")
    def fresh_session(self):
        resp = client.post("/cap/hire", json=HIRE_PAYLOAD)
        assert resp.status_code == 200
        return resp.json()

    def _payload(self, session_id: str) -> dict:
        return {
            "session_id": session_id,
            "tx_hash": "0xabc123def456789000000000000000000000000000000000000000000000001",
            "from_address": "0xCallerWallet0000000000000000000000000001",
            "to_address": SETTLEMENT_ADDRESS,
            "fee_units": FEE_UNITS_PER_CALL,
        }

    def _new_session(self) -> dict:
        return client.post("/cap/hire", json=HIRE_PAYLOAD).json()

    def test_returns_200(self, fresh_session):
        resp = client.post("/cap/settle", json=self._payload(fresh_session["session_id"]))
        assert resp.status_code == 200

    def test_response_shape(self):
        sid = self._new_session()["session_id"]
        body = client.post("/cap/settle", json=self._payload(sid)).json()
        for key in ("settlement_id", "session_id", "status", "confirmed_block", "timestamp", "receipt"):
            assert key in body

    def test_status_is_settled(self):
        sid = self._new_session()["session_id"]
        assert client.post("/cap/settle", json=self._payload(sid)).json()["status"] == "settled"

    def test_settlement_id_prefix(self):
        sid = self._new_session()["session_id"]
        assert client.post("/cap/settle", json=self._payload(sid)).json()["settlement_id"].startswith("settle-")

    def test_confirmed_block_positive(self):
        sid = self._new_session()["session_id"]
        block = client.post("/cap/settle", json=self._payload(sid)).json()["confirmed_block"]
        assert isinstance(block, int) and block > 0

    def test_receipt_tx_hash(self):
        sid = self._new_session()["session_id"]
        payload = self._payload(sid)
        receipt = client.post("/cap/settle", json=payload).json()["receipt"]
        assert receipt["tx_hash"] == payload["tx_hash"]

    def test_receipt_cap_protocol_version(self):
        sid = self._new_session()["session_id"]
        receipt = client.post("/cap/settle", json=self._payload(sid)).json()["receipt"]
        assert receipt["cap_protocol_version"] == "CAP/1.0"

    def test_double_settle_returns_409(self):
        sid = self._new_session()["session_id"]
        payload = self._payload(sid)
        client.post("/cap/settle", json=payload)
        assert client.post("/cap/settle", json=payload).status_code == 409

    def test_unknown_session_returns_404(self):
        assert client.post("/cap/settle", json=self._payload("cap-sess-does-not-exist")).status_code == 404

    def test_wrong_to_address_returns_400(self):
        sid = self._new_session()["session_id"]
        payload = {**self._payload(sid), "to_address": "0xWrong000000000000000000000000000000001"}
        assert client.post("/cap/settle", json=payload).status_code == 400

    def test_insufficient_fee_returns_402(self):
        sid = self._new_session()["session_id"]
        payload = {**self._payload(sid), "fee_units": 1}
        assert client.post("/cap/settle", json=payload).status_code == 402

    def test_session_marked_settled_after_payment(self):
        sid = self._new_session()["session_id"]
        client.post("/cap/settle", json=self._payload(sid))
        body = client.get(f"/cap/session/{sid}").json()
        assert body["settled"] is True
        assert body["status"] == "settled"


# ══════════════════════════════════════════════════════════════════════════════
# Full A2A swarm lifecycle: hire → verify (billed + swarm) → settle
# ══════════════════════════════════════════════════════════════════════════════

class TestFullSwarmLifecycle:
    def test_complete_hire_verify_settle_flow(self):
        # 1 — Hire
        hire = client.post("/cap/hire", json=HIRE_PAYLOAD)
        assert hire.status_code == 200
        session_id = hire.json()["session_id"]

        # 2 — Verify (swarm orchestrator path, CAP billed)
        verify = client.post("/verify", json={
            "text": CREDIBLE_TEXT,
            "session_id": session_id,
        })
        assert verify.status_code == 200
        v = verify.json()
        assert v["cap_billed"] is True
        assert "[SemanticAnalysisAgent]" in v["summary"]
        assert "authoritative source" in v["summary"]
        assert 0.0 <= v["overall_credibility_score"] <= 1.0
        assert 0.0 <= v["confidence"] <= 1.0
        assert len(v["dimensions"]) == 6

        # 3 — Settle
        settle = client.post("/cap/settle", json={
            "session_id": session_id,
            "tx_hash": "0xfullswarmtest000000000000000000000000000000000000000000001",
            "from_address": "0xCallerWallet0000000000000000000000000001",
            "to_address": SETTLEMENT_ADDRESS,
            "fee_units": FEE_UNITS_PER_CALL,
        })
        assert settle.status_code == 200
        assert settle.json()["status"] == "settled"

        # 4 — Confirm session ledger
        session = client.get(f"/cap/session/{session_id}").json()
        assert session["settled"] is True
