import pytest
from models import VerificationResult

@pytest.fixture
def mock_llm_response():
    class MockResponse:
        content = "Mocked LLM answer based on context."
    return MockResponse()

@pytest.fixture
def mock_verification_result():
    return VerificationResult(status="Verified", reason="Mock verification passed.")

@pytest.fixture
def sample_docs():
    return [
        {"content": "Document 1 content about scholarships.", "metadata": {"source": "doc1.pdf"}},
        {"content": "Document 2 content about AICTE.", "metadata": {"source": "doc2.pdf"}}
    ]
