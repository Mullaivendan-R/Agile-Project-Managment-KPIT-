"""
Optional integration tests against the running API and local agile_pm.db.

Run only when the backend is up and you intend to hit the real dev database:

    set AGILE_PM_LIVE=1
    pytest backend/tests/test_live_sync.py -v

Creates a temporary project and deletes it; does not modify existing records.
"""

import os
import sqlite3

import httpx
import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("AGILE_PM_LIVE") != "1",
    reason="Set AGILE_PM_LIVE=1 to run against live server and agile_pm.db",
)

API_BASE = os.environ.get("AGILE_PM_API", "http://127.0.0.1:8000/api")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "agile_pm.db")


def test_live_api_sqlite_create_read_delete_cycle():
    assert os.path.isfile(DB_PATH), f"Expected SQLite file at {DB_PATH}"

    with httpx.Client(base_url=API_BASE, timeout=15.0) as client:
        health = client.get("/health")
        assert health.status_code == 200

        create = client.post(
            "/projects",
            json={
                "name": "__QA_TEMP_PROJECT__",
                "description": "Automated live sync test",
                "status": "PLANNING",
            },
        )
        assert create.status_code == 201, create.text
        project_id = create.json()["id"]

        conn = sqlite3.connect(DB_PATH)
        try:
            row = conn.execute(
                "SELECT name FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            assert row is not None
            assert row[0] == "__QA_TEMP_PROJECT__"

            fetched = client.get(f"/projects/{project_id}")
            assert fetched.status_code == 200
            assert fetched.json()["name"] == "__QA_TEMP_PROJECT__"

            delete = client.delete(f"/projects/{project_id}")
            assert delete.status_code == 204

            assert (
                conn.execute(
                    "SELECT id FROM projects WHERE id = ?", (project_id,)
                ).fetchone()
                is None
            )
        finally:
            conn.close()
