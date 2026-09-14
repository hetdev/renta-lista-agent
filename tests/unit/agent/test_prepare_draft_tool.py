from __future__ import annotations

import pytest
from pydantic import ValidationError

from rentalista.agent.agent import draft_prompt, prepare_draft
from rentalista.ingestion.demo_pipeline import DEMO_CASE_ID, DEMO_PROFILE, default_demo_amounts


def _payload() -> dict:
    return {
        "case_id": DEMO_CASE_ID,
        "profile": DEMO_PROFILE,
        "amounts": default_demo_amounts(),
        "dependents": 1,
        "previous_filing": "FIRST",
    }


def test_prepare_draft_accepts_plain_dict_as_strands_passes_it() -> None:
    # Strands hands tool arguments to the function as dicts, not Pydantic models.
    out = prepare_draft(_payload())
    assert out["must_file"] is True
    assert out["saldo_a_favor"] == 3_709_000
    assert out["cells"]["116"]["amount_cop"] == 926_000


def test_prepare_draft_rejects_bad_payload() -> None:
    with pytest.raises(ValidationError):
        prepare_draft({"case_id": DEMO_CASE_ID})


def test_draft_prompt_forbids_model_arithmetic() -> None:
    prompt = draft_prompt(_payload())
    assert "prepare_draft" in prompt
    assert "Do not compute" in prompt
