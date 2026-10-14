def test_logs_round_trip_and_time_filter(client):
    created = client.post(
        "/v1/ingest/logs",
        json=[
            _log("2026-10-14T00:00:00Z", "checkout", "info", "started"),
            _log("2026-10-14T02:00:00Z", "checkout", "error", "payment failed"),
        ],
    )
    assert created.status_code == 200
    assert created.json()["inserted"] == 2

    listed = client.get("/v1/query/logs", params={"service": "checkout", "level": "error"})
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) == 1
    assert body[0]["message"] == "payment failed"
    assert body[0]["id"]

    window = client.get(
        "/v1/query/logs",
        params={"service": "checkout", "from": "2026-10-14T01:00:00Z"},
    )
    assert [item["message"] for item in window.json()] == ["payment failed"]


def test_metrics_query_and_rollup(client):
    created = client.post(
        "/v1/ingest/metrics",
        json=[
            _metric("2026-10-14T00:00:00Z", "checkout", "latency_ms", 10),
            _metric("2026-10-14T00:01:00Z", "checkout", "latency_ms", 30),
        ],
    )
    assert created.status_code == 200
    assert created.json()["inserted"] == 2

    listed = client.get("/v1/query/metrics", params={"service": "checkout", "name": "latency_ms"})
    assert [item["value"] for item in listed.json()] == [30, 10]

    rollup = client.get(
        "/v1/query/metrics/rollup",
        params={"service": "checkout", "name": "latency_ms"},
    )
    assert rollup.status_code == 200
    assert rollup.json() == {"count": 2, "avg": 20, "min": 10, "max": 30}


def test_threshold_rule_creates_one_alert(client):
    rule = client.post(
        "/v1/alerts/rules",
        json={
            "service": "checkout",
            "metric_name": "cpu",
            "comparison": ">",
            "threshold": 80,
            "window_seconds": 300,
        },
    )
    assert rule.status_code == 200
    rule_id = rule.json()["id"]

    below = client.post(
        "/v1/ingest/metrics",
        json=[_metric("2026-10-14T00:00:00Z", "checkout", "cpu", 10)],
    )
    assert below.status_code == 200
    assert client.get("/v1/alerts").json() == []

    # 00:10 is outside the 5-minute window that started at 00:00, so the
    # earlier sample must not pull the average back under the threshold.
    above = client.post(
        "/v1/ingest/metrics",
        json=[
            _metric("2026-10-14T00:10:00Z", "checkout", "cpu", 90),
            _metric("2026-10-14T00:11:00Z", "checkout", "cpu", 95),
        ],
    )
    assert above.status_code == 200

    alerts = client.get("/v1/alerts", params={"service": "checkout"})
    assert alerts.status_code == 200
    body = alerts.json()
    assert len(body) == 1
    assert body[0]["rule_id"] == rule_id
    assert body[0]["value"] == 92.5

    again = client.post(
        "/v1/ingest/metrics",
        json=[_metric("2026-10-14T00:12:00Z", "checkout", "cpu", 99)],
    )
    assert again.status_code == 200
    assert len(client.get("/v1/alerts", params={"service": "checkout"}).json()) == 1


def _log(timestamp: str, service: str, level: str, message: str) -> dict:
    return {
        "timestamp": timestamp,
        "service": service,
        "level": level,
        "message": message,
        "request_id": "req-1",
        "label": {"host": "web-1"},
    }


def _metric(timestamp: str, service: str, name: str, value: float) -> dict:
    return {
        "timestamp": timestamp,
        "service": service,
        "metric_name": name,
        "value": value,
        "tags": {"host": "web-1"},
    }
