"""Health check and manual notification worker endpoint tests."""


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "service" in body


def test_trigger_notification_worker(client):
    response = client.post("/api/notifications/run-worker")
    assert response.status_code == 200
    body = response.json()
    assert "checked_tasks" in body
    assert "notifications_created" in body
    assert isinstance(body["checked_tasks"], int)
    assert isinstance(body["notifications_created"], int)
