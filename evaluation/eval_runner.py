import json
import logging
import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

from main import RAGPipeline

logger = logging.getLogger(__name__)

def load_dataset(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def run_evaluation():
    pipeline = RAGPipeline()
    dataset_path = os.path.join(os.path.dirname(__file__), "test_dataset.json")
    test_cases = load_dataset(dataset_path)
    
    questions = []
    ground_truths = []
    answers = []
    contexts = []
    
    logger.info("Running queries through the RAG pipeline...")
    for idx, case in enumerate(test_cases):
        q = case["question"]
        logger.info(f"Processing query {idx+1}/{len(test_cases)}: {q}")
        
        relevant_docs = pipeline.retriever.retrieve(q)
        answer = pipeline.generator.generate_answer(q, relevant_docs)
        
        questions.append(q)
        ground_truths.append(case["ground_truth"])
        answers.append(answer)
        contexts.append([doc["content"] for doc in relevant_docs])
        
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    
    hf_dataset = Dataset.from_dict(data)
    
    logger.info("Running RAGAS evaluation metrics...")
    
    # Try using wrappers if Ragas version requires it, else pass native models
    try:
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        eval_llm = LangchainLLMWrapper(pipeline.generator.llm)
        eval_embeddings = LangchainEmbeddingsWrapper(pipeline.retriever.embeddings)
        
        result = evaluate(
            hf_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=eval_llm,
            embeddings=eval_embeddings
        )
    except ImportError:
        # Fallback for older raga versions
        result = evaluate(
            hf_dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )
    
    result_dict = {}
    avg_metrics = {}
    if hasattr(result, 'to_pandas'): 
        df = result.to_pandas()
        result_dict = df.to_dict(orient="records")
        avg_metrics = {
            "faithfulness": df["faithfulness"].mean() if "faithfulness" in df else 0,
            "answer_relevancy": df["answer_relevancy"].mean() if "answer_relevancy" in df else 0,
            "context_precision": df["context_precision"].mean() if "context_precision" in df else 0,
            "context_recall": df["context_recall"].mean() if "context_recall" in df else 0,
        }
    else:
        avg_metrics = result
    
    out_path = os.path.join(os.path.dirname(__file__), "results.json")
    with open(out_path, "w") as f:
        json.dump({"summary": avg_metrics, "details": result_dict}, f, indent=2)
        
    logger.info(f"Evaluation complete. Results saved to {out_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_evaluation()
