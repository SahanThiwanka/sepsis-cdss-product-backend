import requests

BASE_URL = "http://127.0.0.1:18080"


def login_as_admin():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "username": "admin",
            "password": "admin123",
        },
        timeout=10,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert "access_token" in data

    return data["access_token"]


def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def test_backend_health():
    response = requests.get(f"{BASE_URL}/api/health", timeout=10)

    assert response.status_code == 200


def test_login_admin():
    token = login_as_admin()

    assert token is not None
    assert len(token) > 20


def test_model_info():
    response = requests.get(f"{BASE_URL}/api/model/info", timeout=10)

    assert response.status_code == 200

    data = response.json()
    assert "model_version" in data or "model_name" in data


def test_system_health():
    token = login_as_admin()

    response = requests.get(
        f"{BASE_URL}/api/system-health/",
        headers=auth_headers(token),
        timeout=10,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["overall_status"] == "healthy"


def test_monitoring():
    token = login_as_admin()

    response = requests.get(
        f"{BASE_URL}/api/monitoring/",
        headers=auth_headers(token),
        timeout=10,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert "total_predictions" in data
    assert "risk_distribution" in data


def test_prediction_workflow():
    token = login_as_admin()

    payload = {
        "patient_id": "TEST_SMOKE_001",
        "observation": {
            "HR": 110,
            "O2Sat": 94,
            "Temp": 38.5,
            "SBP": 95,
            "MAP": 65,
            "DBP": 55,
            "Resp": 24,
            "WBC": 14,
            "Lactate": 2.5,
            "Age": 65,
            "Gender": 1,
            "Unit1": 1,
            "Unit2": 0,
            "HospAdmTime": -10,
            "ICULOS": 12,
        },
    }

    response = requests.post(
        f"{BASE_URL}/api/predictions/predict",
        json=payload,
        headers=auth_headers(token),
        timeout=30,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["patient_id"] == "TEST_SMOKE_001"
    assert "calibrated_probability" in data
    assert "risk_level" in data
    assert "clinical_rules" in data
    assert "decision_support" in data