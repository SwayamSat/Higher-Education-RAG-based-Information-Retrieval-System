import pytest
from unittest.mock import patch
from main import RAGPipeline
from models import VerificationResult

def test_pipeline_process_query(sample_docs):
    with patch('main.QueryRouter') as MockRouter, \
         patch('main.RelevanceAgent') as MockRetriever, \
         patch('main.GeneratorAgent') as MockGenerator, \
         patch('main.FactCheckAgent') as MockVerifier:
         
        mock_router = MockRouter.return_value
        mock_router.route.return_value = "rag"
        
        mock_retriever = MockRetriever.return_value
        mock_retriever.retrieve.return_value = sample_docs
        
        mock_generator = MockGenerator.return_value
        mock_generator.generate_answer.return_value = "Generated answer."
        
        mock_verifier = MockVerifier.return_value
        mock_verifier.verify.return_value = VerificationResult(status="Verified", reason="OK")
        
        pipeline = RAGPipeline()
        response = pipeline.process_query("What is the scholarship?")
        
        # main.py currently formats output as a string. Assert substring presence.
        assert "Generated answer" in response
        assert "Verified" in response
        assert "doc1.pdf" in response
