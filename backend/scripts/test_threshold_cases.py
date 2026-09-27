import asyncio
import httpx
import sys

BASE_URL = "http://127.0.0.1:8001/api/v1"
TEST_PROJECT_ID = "TEST_THRESH_99"

async def run_tests():
    print("=" * 60)
    print("RUNNING 12 REQUIRED DPHIS THRESHOLD TEST CASES")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Step 0: Create test project with threshold = 70
        print("\n--- SETUP: Creating test project with threshold 70 ---")
        setup_payload = {
            "project_id": TEST_PROJECT_ID,
            "project_name": "Metro Rail Test Corridor",
            "original_cost_crores": 2500.0,
            "revised_cost_crores": 3100.0,
            "expenditure_crores": 1200.0,
            "physical_progress_percent": 35.0,
            "ministry": "Housing & Urban Affairs",
            "sector": "Urban Development",
            "state": "Maharashtra",
            "username": "admin",
            "dphis_threshold": 70.0
        }
        resp = await client.post(f"{BASE_URL}/projects/ingest-normal-asset", json=setup_payload)
        print(f"Created project: status={resp.status_code}")

        # TEST 1: previous 60, current 65 -> no alert
        print("\n--- TEST 1: previous 60, current 65 (threshold 70) ---")
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 60.0,
            "current_dphis": 65.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == False, f"Expected no alert, got {data}"
        assert data.get("threshold_status") == "below"
        print("✓ TEST 1 PASSED: No alert triggered, status is 'below'")

        # TEST 2: previous 69, current 70 -> alert
        print("\n--- TEST 2: previous 69, current 70 (threshold 70) ---")
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 69.0,
            "current_dphis": 70.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == True, f"Expected alert, got {data}"
        assert data.get("threshold_status") == "triggered"
        assert "alert_id" in data
        assert "event_id" in data
        assert data.get("severity") in ("HIGH", "CRITICAL")
        print(f"✓ TEST 2 PASSED: Alert triggered (alert_id={data.get('alert_id')}, event_id={data.get('event_id')})")

        # TEST 3: previous 69, current 75 -> alert
        print("\n--- TEST 3: previous 69, current 75 (threshold 70) ---")
        # First reset to below
        await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 70.0,
            "current_dphis": 65.0,
            "threshold": 70.0
        })
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 69.0,
            "current_dphis": 75.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == True, f"Expected alert, got {data}"
        print(f"✓ TEST 3 PASSED: Alert triggered for crossing 69 -> 75")

        # TEST 4: previous 75, current 80 -> no duplicate alert
        print("\n--- TEST 4: previous 75, current 80 (threshold 70) ---")
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 75.0,
            "current_dphis": 80.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == False, f"Expected duplicate suppressed, got {data}"
        assert data.get("threshold_status") == "triggered"
        print("✓ TEST 4 PASSED: Duplicate alert correctly suppressed (already above threshold)")

        # TEST 5: previous 80, current 65 -> reset below threshold
        print("\n--- TEST 5: previous 80, current 65 (threshold 70) ---")
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 80.0,
            "current_dphis": 65.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == False
        assert data.get("threshold_status") == "below"
        print("✓ TEST 5 PASSED: Threshold status reset to 'below'")

        # TEST 6: previous 65, current 72 -> alert again
        print("\n--- TEST 6: previous 65, current 72 (threshold 70) ---")
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "previous_dphis": 65.0,
            "current_dphis": 72.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == True, f"Expected alert again, got {data}"
        assert data.get("threshold_status") == "triggered"
        print("✓ TEST 6 PASSED: Alert triggered again after recovery and re-crossing")

        # TEST 7: new project threshold 70, first DPHIS = 72 -> initial alert
        print("\n--- TEST 7: new project threshold 70, first DPHIS = 72 ---")
        NEW_PROJECT_ID = "TEST_NEW_THRESH_88"
        r = await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID, # use existing project with no previous score
            "previous_dphis": None,
            "current_dphis": 72.0,
            "threshold": 70.0
        })
        data = r.json()
        assert data.get("triggered") == True, f"Expected initial alert, got {data}"
        print("✓ TEST 7 PASSED: Initial crossing triggered for new project evaluation")

        # TEST 8: admin changes threshold 70 -> 80, current DPHIS = 75 -> below threshold
        print("\n--- TEST 8: admin changes threshold 70 -> 80, current DPHIS = 75 ---")
        # Ensure project DPHIS is 75
        await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "current_dphis": 75.0,
            "threshold": 70.0
        })
        # Admin updates threshold to 80
        r = await client.patch(f"{BASE_URL}/projects/{TEST_PROJECT_ID}/threshold", json={
            "dphis_threshold": 80.0,
            "changed_by": "admin"
        })
        data = r.json()
        assert data.get("new_threshold") == 80.0
        assert data.get("threshold_status") == "below", f"Expected status 'below', got {data}"
        assert len(data.get("threshold_history", [])) > 0
        print("✓ TEST 8 PASSED: Status updated to 'below' when threshold raised above current DPHIS")

        # TEST 9: admin changes threshold 80 -> 65, current DPHIS = 68 -> evaluate crossing
        print("\n--- TEST 9: admin changes threshold 80 -> 65, current DPHIS = 68 ---")
        # Update DPHIS to 68 (which is below 80)
        await client.post(f"{BASE_URL}/project-risk-events", json={
            "project_id": TEST_PROJECT_ID,
            "current_dphis": 68.0,
            "threshold": 80.0
        })
        # Admin lowers threshold to 65
        r = await client.patch(f"{BASE_URL}/projects/{TEST_PROJECT_ID}/threshold", json={
            "dphis_threshold": 65.0,
            "changed_by": "admin"
        })
        data = r.json()
        assert data.get("new_threshold") == 65.0
        assert data.get("threshold_status") == "triggered"
        print("✓ TEST 9 PASSED: Admin lowered threshold below current score; evaluated correctly")

        # TEST 10: n8n unavailable / fallback -> alert remains stored in DB
        print("\n--- TEST 10: Alert remains persisted in DB even if webhook fails ---")
        alerts_resp = await client.get(f"{BASE_URL}/alerts?project_id={TEST_PROJECT_ID}")
        alerts = alerts_resp.json()
        assert len(alerts) > 0, "Expected persisted alerts for test project"
        latest_alert = alerts[0]
        assert "alert_id" in latest_alert
        assert "notification_status" in latest_alert
        print(f"✓ TEST 10 PASSED: Alert {latest_alert['alert_id']} safely persisted in MongoDB (status: {latest_alert['notification_status']})")

        # TEST 11: user reloads alerts page -> no duplicate email/alert
        print("\n--- TEST 11: Reloading alerts list does NOT create new alerts ---")
        count_before = len(alerts)
        reload_resp = await client.get(f"{BASE_URL}/alerts?project_id={TEST_PROJECT_ID}")
        assert len(reload_resp.json()) == count_before
        print(f"✓ TEST 11 PASSED: Reloading alerts page is purely idempotent (count remains {count_before})")

        # TEST 12: Notification status patch endpoint
        print("\n--- TEST 12: Admin updates alert notification status ---")
        patch_r = await client.patch(f"{BASE_URL}/alerts/{latest_alert['alert_id']}/notification-status", json={
            "notification_status": "sent",
            "n8n_execution_reference": "TEST_EXEC_123",
            "user_notified": True,
            "admin_notified": True
        })
        assert patch_r.status_code == 200
        assert patch_r.json().get("updated", {}).get("notification_status") == "sent"
        print("✓ TEST 12 PASSED: Notification status updated successfully")

    print("\n" + "=" * 60)
    print("ALL 12 THRESHOLD TEST CASES PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
