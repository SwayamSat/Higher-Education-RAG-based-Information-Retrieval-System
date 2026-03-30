"""
RAGAS Evaluation — Phase 2 (metrics computation)
=================================================
Loads pipeline outputs already saved in results.json, then:
  • faithfulness / context_precision / context_recall  via RAGAS + Ollama
  • answer_relevancy  via cosine similarity (FastEmbed, no LLM needed)

Usage:
    uv run python evaluation/compute_metrics.py
"""

import json
import logging
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL  = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL_NAME   = os.getenv("LLM_MODEL_NAME", "llama3.2")
EMBED_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")

INTERMEDIATE_PATH = os.path.join(os.path.dirname(__file__), "results.json")
OUTPUT_PATH       = os.path.join(os.path.dirname(__file__), "results.json")


# ── LLM-BASED METRICS VIA RAGAS ──────────────────────────────────────────────

def compute_llm_metrics(questions, answers, contexts_list, ground_truths):
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, context_precision, context_recall
    from langchain_ollama import ChatOllama
    from ragas.llms import LangchainLLMWrapper
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    hf_dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts_list,
        "ground_truth": ground_truths,
    })

    judge_llm = LangchainLLMWrapper(
        ChatOllama(
            model=LLM_MODEL_NAME,
            base_url=OLLAMA_BASE_URL,
            temperature=0.0,
            timeout=180,
        )
    )
    # FastEmbed for any embedding calls within RAGAS
    judge_emb = LangchainEmbeddingsWrapper(
        FastEmbedEmbeddings(model_name=EMBED_MODEL_NAME)
    )

    logger.info("Running RAGAS (faithfulness, context_precision, context_recall)…")
    result = evaluate(
        dataset=hf_dataset,
        metrics=[faithfulness, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_emb,
    )
    df = result.to_pandas()
    logger.info("RAGAS done.")
    return df


# ── MANUAL ANSWER RELEVANCY (cosine sim) ─────────────────────────────────────

def compute_answer_relevancy(questions, answers):
    """
    Measure how relevant the answer is to the question without needing
    an LLM. We embed both and compute cosine similarity.
    Score = cos_sim(embed(question), embed(answer))  ∈ [0, 1]
    """
    from fastembed import TextEmbedding
    import numpy as np

    logger.info(f"Computing answer_relevancy with FastEmbed ({EMBED_MODEL_NAME})…")
    model = TextEmbedding(model_name=EMBED_MODEL_NAME)

    q_embeddings  = list(model.embed(questions))
    a_embeddings  = list(model.embed(answers))

    scores = []
    for q_vec, a_vec in zip(q_embeddings, a_embeddings):
        q_arr = np.array(q_vec)
        a_arr = np.array(a_vec)
        norm = (np.linalg.norm(q_arr) * np.linalg.norm(a_arr))
        cos_sim = float(np.dot(q_arr, a_arr) / norm) if norm > 0 else 0.0
        # Clamp to [0,1] — cosine can be negative for unrelated texts
        scores.append(max(0.0, round(cos_sim, 4)))

    logger.info(f"Answer relevancy scores: {scores}")
    return scores


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Phase 2 — RAGAS Metric Computation")
    logger.info("=" * 60)

    # Load intermediate data
    with open(INTERMEDIATE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    questions     = data["questions"]
    answers       = data["answers"]
    contexts_list = data["contexts"]
    ground_truths = data["ground_truths"]
    logger.info(f"Loaded {len(questions)} Q&A pairs from {INTERMEDIATE_PATH}")

    # ── LLM metrics ───────────────────────────────────────────────────────────
    df = compute_llm_metrics(questions, answers, contexts_list, ground_truths)

    per_question = df.to_dict(orient="records")

    def safe_mean(col):
        return round(float(df[col].mean()), 4) if col in df.columns else None

    # ── Answer relevancy (cosine) ─────────────────────────────────────────────
    ar_scores = compute_answer_relevancy(questions, answers)
    avg_ar = round(sum(ar_scores) / len(ar_scores), 4)

    # Inject into per-question records
    for i, rec in enumerate(per_question):
        rec["answer_relevancy"] = ar_scores[i] if i < len(ar_scores) else None

    summary = {
        "faithfulness":      safe_mean("faithfulness"),
        "answer_relevancy":  avg_ar,
        "context_precision": safe_mean("context_precision"),
        "context_recall":    safe_mean("context_recall"),
    }

    # ── Save ──────────────────────────────────────────────────────────────────
    full_output = {
        "summary":       summary,
        "per_question":  per_question,
        "questions":     questions,
        "answers":       answers,
        "contexts":      contexts_list,
        "ground_truths": ground_truths,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, default=str)

    # ── Print table ───────────────────────────────────────────────────────────
    labels = {
        "faithfulness":      "Faithfulness",
        "answer_relevancy":  "Answer Relevancy",
        "context_precision": "Context Precision",
        "context_recall":    "Context Recall",
    }
    print("\n" + "═" * 62)
    print("  RAGAS PERFORMANCE METRICS — FINAL RESULTS")
    print("═" * 62)
    for key, label in labels.items():
        score = summary.get(key)
        if score is not None:
            bar = "█" * int(score * 20)
            print(f"  {label:<22}  {score:.4f}  {bar}")
        else:
            print(f"  {label:<22}  N/A")
    print("═" * 62)
    print(f"\nFull results → {OUTPUT_PATH}\n")

    return summary


if __name__ == "__main__":
    main()
