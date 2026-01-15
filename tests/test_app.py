import pytest
from app.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

    def test_index(client):
        rv = client.get('/')
        assert b"MLB Probability & Value Tracker" in rv.data
def test_standings(client):
    rv = client.get('/standings')
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert isinstance(json_data, dict)
    # Check for a known division ID (e.g., AL East or similar structure)
    # The structure returned by standings_data uses division IDs as keys (e.g. "201", "202")
    assert any(key in json_data for key in ["201", "202", "203", "204", "205", "200"])
