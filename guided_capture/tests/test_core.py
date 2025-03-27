"""
Tests for the GuidedCapture core functionality.
"""

import pytest
from unittest.mock import MagicMock, patch
from guided_capture import GuidedCapture

class MockLLMClient:
    """Mock LLM client for testing."""
    def __init__(self):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()

    def create_completion(self, *args, **kwargs):
        return MagicMock(
            choices=[MagicMock(message=MagicMock(content='["Test Question 1?", "Test Question 2?"]'))]
        )

@pytest.fixture
def mock_llm():
    """Fixture providing a mock LLM client."""
    return MockLLMClient()

@pytest.fixture
def capture(mock_llm):
    """Fixture providing a GuidedCapture instance."""
    return GuidedCapture(
        topic="Test Topic",
        output_format_description="Test Output Format",
        llm_client=mock_llm
    )

def test_initialization(capture):
    """Test that GuidedCapture initializes correctly."""
    assert capture.topic == "Test Topic"
    assert capture.output_format_description == "Test Output Format"
    assert capture.num_questions == 5  # default value
    assert not capture._questions_generated
    assert not capture._synthesis_complete
    assert capture.final_output is None
    assert capture.questions == []
    assert capture.answers == {}

def test_generate_questions(capture, mock_llm):
    """Test question generation."""
    questions = capture.generate_questions()
    assert len(questions) == 2
    assert "Test Question 1?" in questions
    assert "Test Question 2?" in questions
    assert capture._questions_generated
    assert all(q in capture.answers for q in questions)

def test_submit_answer(capture):
    """Test submitting a single answer."""
    capture.generate_questions()
    question = capture.questions[0]
    answer = "Test Answer"
    capture.submit_answer(question, answer)
    assert capture.answers[question] == answer
    assert not capture._synthesis_complete
    assert capture.final_output is None

def test_submit_answers_bulk(capture):
    """Test submitting multiple answers at once."""
    capture.generate_questions()
    answers = {q: f"Answer for {q}" for q in capture.questions}
    capture.submit_answers_bulk(answers)
    assert all(capture.answers[q] == a for q, a in answers.items())
    assert not capture._synthesis_complete
    assert capture.final_output is None

def test_get_missing_questions(capture):
    """Test getting list of unanswered questions."""
    capture.generate_questions()
    assert len(capture.get_missing_questions()) == len(capture.questions)
    capture.submit_answer(capture.questions[0], "Answer")
    assert len(capture.get_missing_questions()) == len(capture.questions) - 1

def test_state_management(capture, mock_llm):
    """Test saving and loading state."""
    capture.generate_questions()
    capture.submit_answer(capture.questions[0], "Answer")
    
    state = capture.get_state()
    assert state["topic"] == capture.topic
    assert state["questions"] == capture.questions
    assert state["answers"] == capture.answers
    
    new_capture = GuidedCapture.load_state(state, mock_llm)
    assert new_capture.topic == capture.topic
    assert new_capture.questions == capture.questions
    assert new_capture.answers == capture.answers

def test_invalid_initialization():
    """Test that invalid initialization raises appropriate errors."""
    with pytest.raises(ValueError):
        GuidedCapture("", "Output", MagicMock())
    with pytest.raises(ValueError):
        GuidedCapture("Topic", "", MagicMock())
    with pytest.raises(TypeError):
        GuidedCapture("Topic", "Output", "not_a_client") 