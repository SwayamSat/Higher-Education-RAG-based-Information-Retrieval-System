import pytest
from unittest.mock import MagicMock, patch
from agents import RelevanceAgent, GeneratorAgent, FactCheckAgent
from models import VerificationResult

def test_relevance_agent_retrieve(sample_docs):
    with patch('agents.RelevanceAgent.__init__', return_value=None):
        agent = RelevanceAgent()
        agent.vector_store = MagicMock()
        agent.index_loaded = False
        
        mock_doc = MagicMock()
        mock_doc.page_content = sample_docs[0]["content"]
        mock_doc.metadata = sample_docs[0]["metadata"]
        
        agent.faiss_retriever = MagicMock()
        agent.faiss_retriever.invoke.return_value = [mock_doc]
        
        results = agent.retrieve("scholarship")
        assert len(results) == 1
        assert results[0]["content"] == sample_docs[0]["content"]
        assert results[0]["metadata"]["source"] == "doc1.pdf"
        assert "score" in results[0]

def test_generator_agent(mock_llm_response, sample_docs):
    with patch('agents.GeneratorAgent.__init__', return_value=None):
        agent = GeneratorAgent()
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = mock_llm_response
        agent.memory = []
        agent.prompt_template = MagicMock()
        agent.prompt_template.format.return_value = "prompt"
        
        with patch('agents.call_llm_with_retry', return_value=mock_llm_response) as mock_retry:
            answer = agent.generate_answer("query", sample_docs)
            assert answer == mock_llm_response.content
            mock_retry.assert_called_once()
            assert len(agent.memory) == 1

def test_fact_check_agent(mock_verification_result, sample_docs):
    with patch('agents.FactCheckAgent.__init__', return_value=None):
        agent = FactCheckAgent()
        agent.llm = MagicMock()
        agent.parser = MagicMock()
        agent.parser.invoke.return_value = mock_verification_result
        agent.verify_prompt = MagicMock()
        agent.verify_prompt.format.return_value = "prompt"
        
        with patch('agents.call_llm_with_retry', return_value=MagicMock()) as mock_retry:
            result = agent.verify("query", "Answer", sample_docs)
            assert isinstance(result, VerificationResult)
            assert result.status == "Verified"
            mock_retry.assert_called_once()
            agent.parser.invoke.assert_called_once()
