import pytest
from pydantic import ValidationError

from main import (
    ChatRequest,
    EssayRequest,
    is_referential_follow_up,
)


def test_detects_referential_follow_up():
    assert is_referential_follow_up(
        "Explain the second point."
    )


def test_detects_pronoun_follow_up():
    assert is_referential_follow_up(
        "What does that mean?"
    )


def test_new_short_topic_is_not_follow_up():
    assert not is_referential_follow_up(
        "How can pricing improve retention?"
    )


def test_long_message_is_not_referential_follow_up():
    message = (
        "Please provide a detailed explanation of activation "
        "metrics and their relationship with customer retention "
        "for a growing software company."
    )

    assert not is_referential_follow_up(message)


def test_chat_request_removes_surrounding_spaces():
    request = ChatRequest(
        message="  Explain activation  "
    )

    assert request.message == "Explain activation"


def test_blank_chat_request_is_rejected():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_essay_topic_removes_surrounding_spaces():
    request = EssayRequest(
        topic="  Product activation strategy  "
    )

    assert request.topic == "Product activation strategy"


def test_short_essay_topic_is_rejected():
    with pytest.raises(ValidationError):
        EssayRequest(topic="AI")