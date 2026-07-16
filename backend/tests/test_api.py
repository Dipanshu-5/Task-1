import pytest
from datetime import date

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "sqlite" in data["database"]

def test_read_hcps(client):
    response = client.get("/api/hcps")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["full_name"] == "Dr. Priya Sharma"
    assert data[1]["full_name"] == "Dr. Alan Grant"

def test_create_interaction(client):
    payload = {
        "hcp_id": 1,
        "interaction_type": "In-Person",
        "interaction_date": str(date.today()),
        "attendees": ["Dr. Priya Sharma", "Sales Rep John"],
        "topics_discussed": ["Product Efficacy", "Safety Profile"],
        "materials_shared": ["Clinical Brochure"],
        "samples_distributed": [{"product": "Product X", "quantity": 10}],
        "sentiment": "Positive",
        "outcomes": "Doctor showed keen interest in prescribing Product X.",
        "follow_up_actions": "Send digital details next week",
        "follow_up_date": str(date.today()),
        "original_notes": "Met Dr. Priya today, very positive meeting.",
        "ai_summary": "In-person interaction with Dr. Priya Sharma on efficacy and safety.",
        "created_by": "System Rep",
        "status": "Submitted"
    }
    response = client.post("/api/interactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["hcp_id"] == 1
    assert data["sentiment"] == "Positive"
    assert "Product X" in str(data["samples_distributed"])

def test_create_interaction_invalid_hcp(client):
    payload = {
        "hcp_id": 999,
        "interaction_type": "In-Person",
        "interaction_date": str(date.today()),
        "sentiment": "Positive"
    }
    response = client.post("/api/interactions", json=payload)
    assert response.status_code == 400
    assert "HCP not found" in response.json()["detail"]

def test_update_interaction(client):
    # Create first
    payload = {
        "hcp_id": 1,
        "interaction_type": "In-Person",
        "interaction_date": str(date.today()),
        "sentiment": "Neutral"
    }
    create_res = client.post("/api/interactions", json=payload)
    assert create_res.status_code == 201
    interaction_id = create_res.json()["id"]

    # Patch updates
    updates = {
        "sentiment": "Positive",
        "outcomes": "Updated outcome text",
        "attendees": ["Dr. Priya", "Rep", "New Attendee"]
    }
    update_res = client.patch(f"/api/interactions/{interaction_id}", json=updates)
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["sentiment"] == "Positive"
    assert data["outcomes"] == "Updated outcome text"
    assert "New Attendee" in data["attendees"]

def test_read_hcp_interaction_history(client):
    # Create an interaction
    payload = {
        "hcp_id": 1,
        "interaction_type": "In-Person",
        "interaction_date": str(date.today()),
        "sentiment": "Positive"
    }
    client.post("/api/interactions", json=payload)

    # Get history
    history_res = client.get("/api/hcps/1/interaction-history")
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 1
    assert history[0]["sentiment"] == "Positive"

def test_agent_chat_stub(client):
    payload = {
        "message": "Met Dr. Priya, very positive",
        "history": [],
        "current_state": {}
    }
    response = client.post("/api/agent/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "extracted_data" in data

def test_agent_extract_stub(client):
    payload = {
        "text": "Met Dr. Priya, very positive"
    }
    response = client.post("/api/agent/extract", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "extracted_data" in data
    assert "compliance_warnings" in data

def test_agent_follow_up_suggestions_stub(client):
    payload = {
        "notes": "Discussed Product X efficacy",
        "sentiment": "Positive"
    }
    response = client.post("/api/agent/follow-up-suggestions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["suggestions"]) > 0
    assert data["is_ai_generated"] is True
