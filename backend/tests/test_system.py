def test_health_reports_data_sources(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    names = {source["name"] for source in body["data_sources"]}
    assert {"FinMind", "TWSE MIS", "Finnhub"} <= names
    finnhub = next(s for s in body["data_sources"] if s["name"] == "Finnhub")
    assert finnhub["configured"] is False


def test_unknown_route_uses_error_format(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "HTTP_404"


def test_cors_allows_frontend_origin(client):
    response = client.get("/api/health", headers={"Origin": "http://localhost:3000"})

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
