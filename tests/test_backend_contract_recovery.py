import pytest
from pydantic import ValidationError

from app.core.exceptions import JourneyVersionConflict
from app.models.interaction import InteractionResponse
from app.models.session import SessionRecord
from app.models.student_model_session import (
    GuidedSupportEvent,
    StudentModelSessionEventResponse,
)
from app.services import session_service
from tests.test_session_events import _session_opened_response


@pytest.mark.parametrize("field", ["routing_reason_code", "support_reason_code"])
def test_student_model_reason_codes_remain_open(field: str) -> None:
    with pytest.raises(ValidationError) as raised:
        InteractionResponse.model_validate({field: "GUIDED_STARTED"})

    assert not [error for error in raised.value.errors() if error["loc"] == (field,)]


def test_journey_conflict_refreshes_the_cached_version() -> None:
    event = StudentModelSessionEventResponse.model_validate(
        _session_opened_response("PHASE_2_GUIDED_LEARNING")
    )
    session = SessionRecord.model_construct(
        session_id="SESSION-CONFLICT",
        student_id="ST001",
        current_phase="GUIDED_PRACTICE",
        student_model_event=event,
        question_id="Q-T02-004",
        active_student_model_question=object(),
    )
    session_service._sessions[session.session_id] = session
    journey = event.journey_state.model_dump(mode="json")
    journey["version"] = event.journey_state.version + 1

    session_service.reconcile_journey_conflict(
        session.session_id,
        session.student_id,
        JourneyVersionConflict({"current_journey_state": journey}),
    )

    refreshed = session_service._sessions[session.session_id]
    assert refreshed.student_model_event.journey_state.version == journey["version"]
    assert refreshed.question_id is None
    assert refreshed.active_student_model_question is None


def test_wrong_four_without_an_error_code_is_generic_support() -> None:
    event = GuidedSupportEvent(
        request_id="REQ-1",
        event_type="GUIDED_SUPPORT_ESCALATION_REQUIRED",
        source_turn_id="TURN-1",
        expected_journey_version=1,
        topic_id="ALG-ORI-02",
        student_id="ST001",
        timestamp="2026-08-12T00:00:00Z",
        question_id="Q-T02-004",
        micro_skill_id="T02.M1",
        triggering_response=None,
        error_code=None,
    )

    assert event.triggering_response is None
    assert event.error_code is None
