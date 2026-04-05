# tests/test_verifier.py
import json
import pytest
from unittest.mock import MagicMock, patch
from verifier import format_facts, verify_collateral, _build_content


def test_format_facts_includes_policy_info():
    facts = [{"policy_info": {"Insurer Name": "Star Health", "Net Premium": "5000000"}}]
    text = format_facts(facts)
    assert "Insurer Name: Star Health" in text
    assert "Net Premium: 5000000" in text


def test_format_facts_includes_plans():
    facts = [{"plans": {"Gold": {"Base SI": "800000", "Room Rent Restriction": "Single Pvt AC Room"}}}]
    text = format_facts(facts)
    assert "Gold" in text
    assert "Base SI: 800000" in text


def test_format_facts_includes_benefits():
    facts = [{"benefits": [{"name": "Dental Care Plan", "premium": 470.0}]}]
    text = format_facts(facts)
    assert "Dental Care Plan" in text
    assert "470" in text


def test_build_content_text_only():
    content = _build_content("prompt text", "", [])
    assert len(content) == 1
    assert content[0]["type"] == "text"


def test_build_content_with_images():
    images = [("base64data", "image/png")]
    content = _build_content("prompt", "", images)
    assert len(content) == 2
    assert content[1]["type"] == "image"
    assert content[1]["source"]["data"] == "base64data"


MOCK_RESPONSE = {
    "summary": "The collateral has one incorrect claim.",
    "check_items": [
        {
            "field_name": "Room Rent",
            "claimed_value": "Single Private Room",
            "actual_value": "2% of SI",
            "status": "incorrect"
        }
    ]
}


def test_verify_collateral_returns_parsed_json(mocker):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(MOCK_RESPONSE))]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    mocker.patch("verifier.anthropic.Anthropic", return_value=mock_client)
    mocker.patch("verifier.st.secrets", {"ANTHROPIC_API_KEY": "test-key"})

    result = verify_collateral("facts text", [], "collateral text", [])
    assert result["summary"] == "The collateral has one incorrect claim."
    assert result["check_items"][0]["status"] == "incorrect"
