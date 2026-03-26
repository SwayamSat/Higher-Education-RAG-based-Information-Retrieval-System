import pytest
from router import QueryRouter

@pytest.fixture
def router():
    return QueryRouter()

def test_route_greeting(router):
    assert router.route("hello") == "direct"
    assert router.route("who are you") == "direct"

def test_route_keyword(router):
    assert router.route("what is the scholarship criteria?") == "rag"
    assert router.route("tell me about aicte guidelines") == "rag"

def test_route_short_ambiguous(router):
    assert router.route("why?") == "clarify"
    assert router.route("tell") == "clarify"

def test_route_math(router):
    assert router.route("2+2") == "direct"
    assert router.route("5 * 5 / 2") == "direct"

def test_route_normal_sentence(router):
    assert router.route("can you describe the situation without specifics of any rules") == "rag"
