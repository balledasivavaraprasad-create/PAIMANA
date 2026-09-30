import pytest
import uuid
import hmac
import hashlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import httpx
from httpx import Response

from app.db.mongodb import connect_to_mongo, get_database
from app.config.settings import settings
from app.services.alert_service import evaluate_project_threshold_crossing
from app.services.notification_automation_service import (
    notification_automation_service,
    compute_hmac_signature,
    verify_hmac_signature
)

@pytest.fixture(autouse=True)
async def setup_db():
    await connect_to_mongo()
    yield

# =========================================================================
# Scenario 1: DPHIS crosses threshold → webhook event generated
# =========================================================================
@pytest.mark.asyncio
async def test_01_dphis_crosses_threshold_generates_webhook_event():
    db = get_database()
    pid = f"P_TEST01_{uuid.uuid4().hex[:6]}"
    
    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Bengaluru Suburban Rail Corridor 2",
            "department": "Railways",
            "sector": "Railways & Urban Transit",
            "state": "Karnataka",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "current_dphis": 61.4,
            "previous_dphis": 61.4
        }},
        upsert=True
    )

    captured_payload = None

    async def mock_post(url, json=None, timeout=None, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        return Response(status_code=200, json={"ok": True, "event_id": json.get("event_id"), "status": "accepted"})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # 61.4 -> 77.2 (threshold 70.0)
        res = await evaluate_project_threshold_crossing(
            project_id=pid,
            previous_dphis=61.4,
            current_dphis=77.2,
            custom_threshold=70.0
        )

        assert res["triggered"] is True
        assert res["threshold_status"] == "triggered"
        assert res["webhook_dispatched"] is True
        assert captured_payload is not None
        assert captured_payload["event_id"] is not None
        assert captured_payload["project"]["project_code"] == pid
        assert captured_payload["risk"]["current_dphis"] == 77.2
        assert captured_payload["risk"]["threshold"] == 70.0
        assert captured_payload["risk"]["risk_tier"] == "High"

# =========================================================================
# Scenario 2: DPHIS already above threshold → no duplicate event
# =========================================================================
@pytest.mark.asyncio
async def test_02_dphis_already_above_threshold_no_duplicate_event():
    db = get_database()
    pid = f"P_TEST02_{uuid.uuid4().hex[:6]}"

    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Western Dedicated Corridor",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "triggered",
            "current_dphis": 74.0,
            "previous_dphis": 71.0
        }},
        upsert=True
    )

    captured_post = False

    async def mock_post(url, json=None, timeout=None, **kwargs):
        nonlocal captured_post
        captured_post = True
        return Response(status_code=200, json={"ok": True})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # 74.0 -> 75.0 (both above threshold 70.0)
        res = await evaluate_project_threshold_crossing(
            project_id=pid,
            previous_dphis=74.0,
            current_dphis=75.0,
            custom_threshold=70.0
        )

        assert res["triggered"] is False
        assert captured_post is False

# =========================================================================
# Scenario 3: Risk acceleration → correct event sent
# =========================================================================
@pytest.mark.asyncio
async def test_03_risk_acceleration_event_sent():
    pid = f"P_TEST03_{uuid.uuid4().hex[:6]}"
    captured_payload = None

    async def mock_post(url, json=None, timeout=None, **kwargs):
        nonlocal captured_payload
        captured_payload = json
        return Response(status_code=200, json={"ok": True, "event_id": json.get("event_id"), "status": "accepted"})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        res = await notification_automation_service.trigger_risk_alert({
            "project_id": pid,
            "event_type": "RISK_ACCELERATING",
            "current_dphis": 76.5,
            "previous_dphis": 52.0,
            "threshold": 70.0,
            "recipient_email": "officer@example.gov.in"
        })

        assert res["ok"] is True
        assert captured_payload is not None
        assert captured_payload["event_type"] == "RISK_ACCELERATING"
        assert "RISK_ACCELERATING" in captured_payload["events"]

# =========================================================================
# Scenario 4: No meaningful change → no webhook
# =========================================================================
@pytest.mark.asyncio
async def test_04_no_meaningful_change_no_webhook():
    db = get_database()
    pid = f"P_TEST04_{uuid.uuid4().hex[:6]}"

    await db.projects.update_one(
        {"project_id": pid},
        {"$set": {
            "project_id": pid,
            "project_name": "Stable Highway Corridor",
            "dphis_threshold": 70.0,
            "threshold_enabled": True,
            "threshold_status": "below",
            "current_dphis": 50.0,
            "previous_dphis": 49.5
        }},
        upsert=True
    )

    captured_post = False

    async def mock_post(url, json=None, timeout=None, **kwargs):
        nonlocal captured_post
        captured_post = True
        return Response(status_code=200, json={"ok": True})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # 50.0 -> 50.5 (below threshold 70.0)
        res = await evaluate_project_threshold_crossing(
            project_id=pid,
            previous_dphis=50.0,
            current_dphis=50.5,
            custom_threshold=70.0
        )

        assert res["triggered"] is False
        assert res["threshold_status"] == "below"
        assert captured_post is False

# =========================================================================
# Scenario 5: Duplicate event_id → no duplicate email / suppressed
# =========================================================================
@pytest.mark.asyncio
async def test_05_duplicate_event_id_no_duplicate_email():
    pid = f"P_TEST05_{uuid.uuid4().hex[:6]}"
    fixed_event_id = f"evt_dup_{uuid.uuid4().hex[:8]}"

    post_count = 0

    async def mock_post(url, json=None, timeout=None, **kwargs):
        nonlocal post_count
        post_count += 1
        return Response(status_code=200, json={"ok": True, "event_id": fixed_event_id, "status": "accepted"})

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        # First send
        res1 = await notification_automation_service.trigger_risk_alert({
            "event_id": fixed_event_id,
            "project_id": pid,
            "current_dphis": 78.0,
            "threshold": 70.0,
            "recipient_email": "officer@example.gov.in"
        })
        assert res1["ok"] is True
        assert post_count == 1

        # Second send with identical event_id
        res2 = await notification_automation_service.trigger_risk_alert({
            "event_id": fixed_event_id,
            "project_id": pid,
            "current_dphis": 78.0,
            "threshold": 70.0,
            "recipient_email": "officer@example.gov.in"
        })
        assert res2["status"] == "duplicate"
        assert post_count == 1  # No duplicate network call

# =========================================================================
# Scenario 6: n8n timeout → retryable outbox event
# =========================================================================
@pytest.mark.asyncio
async def test_06_n8n_timeout_retryable_outbox_event():
    db = get_database()
    pid = f"P_TEST06_{uuid.uuid4().hex[:6]}"

    async def mock_timeout(url, json=None, timeout=None, **kwargs):
        raise httpx.TimeoutException("Connection to n8n timed out after 8.0s")

    with patch("httpx.AsyncClient.post", side_effect=mock_timeout):
        res = await notification_automation_service.trigger_risk_alert({
            "project_id": pid,
            "current_dphis": 75.0,
            "threshold": 70.0,
            "recipient_email": "officer@example.gov.in"
        })

        assert res["delivery_status"] == "failed_retryable"
        assert res["webhook_dispatched"] is False

        # Verify persisted in outbox
        outbox_doc = await db.outbox_events.find_one({"outbox_id": res["outbox_id"]})
        assert outbox_doc is not None
        assert outbox_doc["status"] == "failed_retryable"
        assert outbox_doc["next_retry_at"] is not None

# =========================================================================
# Scenario 7: n8n 500 → retryable outbox event
# =========================================================================
@pytest.mark.asyncio
async def test_07_n8n_500_retryable():
    db = get_database()
    pid = f"P_TEST07_{uuid.uuid4().hex[:6]}"

    async def mock_500(url, json=None, timeout=None, **kwargs):
        return Response(status_code=500, text="Internal Worker Out of Memory")

    with patch("httpx.AsyncClient.post", side_effect=mock_500):
        res = await notification_automation_service.trigger_risk_alert({
            "project_id": pid,
            "current_dphis": 79.0,
            "threshold": 70.0,
            "recipient_email": "officer@example.gov.in"
        })

        assert res["delivery_status"] == "failed_retryable"
        assert res["status_code"] == 500

        outbox_doc = await db.outbox_events.find_one({"outbox_id": res["outbox_id"]})
        assert outbox_doc is not None
        assert outbox_doc["status"] == "failed_retryable"

# =========================================================================
# Scenario 8: Malformed payload → rejected safely
# =========================================================================
@pytest.mark.asyncio
async def test_08_malformed_payload_rejected():
    # Missing project_id
    res = await notification_automation_service.trigger_risk_alert({
        "current_dphis": 75.0,
        "recipient_email": "officer@example.gov.in"
    })
    assert res["success"] is False
    assert res["status"] == "validation_failed"

    # Missing current_dphis
    res2 = await notification_automation_service.trigger_risk_alert({
        "project_id": "P_INVALID",
        "recipient_email": "officer@example.gov.in"
    })
    assert res2["success"] is False
    assert res2["status"] == "validation_failed"

# =========================================================================
# Scenario 9: Invalid signature → rejected / verification fails
# =========================================================================
def test_09_invalid_signature_rejected():
    secret = "production-secret-test-key-2026"
    payload = b'{"event_id": "evt_test", "dphis": 75.0}'

    valid_sig = compute_hmac_signature(payload, secret)
    assert valid_sig.startswith("sha256=")

    # Correct signature verifies
    assert verify_hmac_signature(payload, valid_sig, secret) is True

    # Tampered signature fails
    tampered_sig = valid_sig[:-4] + "ffff"
    assert verify_hmac_signature(payload, tampered_sig, secret) is False

    # Wrong secret fails
    assert verify_hmac_signature(payload, valid_sig, "wrong-secret") is False

    # Empty signature fails
    assert verify_hmac_signature(payload, "", secret) is False

# =========================================================================
# Scenario 10: Missing recipient email → alert generation fails safely
# =========================================================================
@pytest.mark.asyncio
async def test_10_missing_recipient_email_fails_safely():
    res = await notification_automation_service.trigger_risk_alert({
        "project_id": "P_NO_EMAIL",
        "current_dphis": 82.0,
        "threshold": 70.0
        # No recipient_email supplied
    })
    assert res["success"] is False
    assert res["status"] == "validation_failed"
    assert "recipient email" in res["error"].lower()

# =========================================================================
# Scenario 11: OpenAI generation failure → fallback email template
# =========================================================================
@pytest.mark.asyncio
async def test_11_openai_generation_failure_uses_fallback_template():
    payload = {
        "event_id": "evt_fallback_1",
        "project": {"project_code": "P_FB_1", "project_name": "Chenab Rail Bridge", "sector": "Railways"},
        "risk": {"current_dphis": 81.2, "previous_dphis": 65.0, "threshold": 70.0, "risk_tier": "Critical"},
        "recipient": {"name": "Senior Engineer", "email": "engineer@ir.gov.in"},
        "predictions": {"predicted_cost_overrun_pct": 14.2, "predicted_schedule_slippage_months": 8.0},
        "progress": {"physical_progress_pct": 52.0, "expenditure_pct": 68.0},
        "links": {"project_url": "https://paimana-seven.vercel.app?project=P_FB_1"}
    }

    # Simulate OpenAI failure by setting mock to raise
    async def mock_openai_fail(url, headers=None, json=None, timeout=None):
        raise httpx.ConnectError("OpenAI API unreachable")

    with patch("httpx.AsyncClient.post", side_effect=mock_openai_fail):
        subj, text, html = await notification_automation_service.generate_ai_email(payload)

        # Subject & text adhere to Section 11 structure
        assert "Chenab Rail Bridge" in subj
        assert "DPHIS threshold crossed" in subj
        assert "81.2" in text
        assert "predicted_cost_overrun" in text.lower() or "predicted cost overrun" in text.lower()
        assert "engineer@ir.gov.in" in text or "Senior Engineer" in text

# =========================================================================
# Scenario 12: Email send failure → retry/log failure via outbox
# =========================================================================
@pytest.mark.asyncio
async def test_12_email_send_failure_retried_and_logged():
    db = get_database()
    outbox_id = f"OBX_RETRY_{uuid.uuid4().hex[:6]}"
    
    # Insert failed retryable event
    await db.outbox_events.insert_one({
        "outbox_id": outbox_id,
        "event_id": f"evt_{uuid.uuid4().hex[:6]}",
        "project_id": "P_RETRY",
        "target_url": "http://localhost:5678/webhook/paimana-risk-alert",
        "headers": {},
        "payload": {"test": "data"},
        "status": "failed_retryable",
        "retry_count": 0,
        "next_retry_at": None,
        "created_at": datetime.now(timezone.utc)
    })

    # Simulate success on retry
    async def mock_retry_ok(url, json=None, timeout=None, **kwargs):
        return Response(status_code=200, json={"ok": True})

    with patch("httpx.AsyncClient.post", side_effect=mock_retry_ok):
        res = await notification_automation_service.process_outbox_retries(max_retries=3)
        assert res["success"] >= 1

        updated = await db.outbox_events.find_one({"outbox_id": outbox_id})
        assert updated["status"] == "dispatched"
        assert updated["retry_count"] == 1

# =========================================================================
# Scenario 13: Optional peer data missing → email still sends
# =========================================================================
def test_13_optional_peer_data_missing_email_still_sends():
    payload = {
        "event_id": "evt_peer_missing",
        "project": {"project_code": "P_NO_PEER", "project_name": "Rural Bridge Network"},
        "risk": {"current_dphis": 74.0, "previous_dphis": 62.0, "threshold": 70.0},
        "recipient": {"name": "Officer", "email": "officer@example.gov.in"},
        "peer_intelligence": {"available": False},  # Peer data absent
        "links": {}
    }

    subj, text, html = notification_automation_service.generate_fallback_email(payload)
    assert "Rural Bridge Network" in subj
    assert "Peer comparison was not used because insufficient comparable projects were available" in text
    assert len(html) > 50

# =========================================================================
# Scenario 14: Optional SHAP data missing → email still sends
# =========================================================================
def test_14_optional_shap_data_missing_email_still_sends():
    payload = {
        "event_id": "evt_shap_missing",
        "project": {"project_code": "P_NO_SHAP", "project_name": "Port Terminal 4"},
        "risk": {"current_dphis": 76.0, "previous_dphis": 60.0, "threshold": 70.0},
        "recipient": {"name": "Officer", "email": "officer@example.gov.in"},
        "explanations": None,  # No SHAP explanations
        "links": {}
    }

    subj, text, html = notification_automation_service.generate_fallback_email(payload)
    assert "Port Terminal 4" in subj
    assert "76.0" in text
    assert html is not None

# =========================================================================
# Scenario 15: Investigation URL unavailable → email still sends safely
# =========================================================================
def test_15_investigation_url_unavailable_email_still_sends():
    payload = {
        "event_id": "evt_no_url",
        "project": {"project_code": "P_NO_URL", "project_name": "Expressway Junction"},
        "risk": {"current_dphis": 72.0, "previous_dphis": 59.0, "threshold": 70.0},
        "recipient": {"name": "Director", "email": "director@morth.gov.in"},
        "links": {}  # Empty links dictionary
    }

    subj, text, html = notification_automation_service.generate_fallback_email(payload)
    assert "Expressway Junction" in subj
    # Default portal links inserted safely
    assert "https://paimana-seven.vercel.app" in text
    assert "https://paimana-seven.vercel.app" in html
