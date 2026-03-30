"""
RAGAS Performance Evaluation — Smart Retrieval of Education System
===================================================================
Runs 10 domain-specific queries directly through the RAG pipeline,
evaluates with RAGAS 0.4.x metrics using:
  • Ollama llama3.2 as judge LLM  (faithfulness, context_precision, context_recall)
  • FastEmbed BAAI/bge-base-en-v1.5 for embeddings (answer_relevancy)

Usage (from project root):
    uv run python evaluation/run_eval.py

Output:
    evaluation/results.json   — per-question breakdown + summary
"""

import json
import logging
import os
import sys
import time

# ── ensure project root is importable ─────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL  = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL_NAME   = os.getenv("LLM_MODEL_NAME", "llama3.2")
EMBED_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
OUTPUT_PATH      = os.path.join(os.path.dirname(__file__), "results.json")

# ── TEST DATASET (10 questions) ───────────────────────────────────────────────
TEST_DATASET = [
    {
        "question": "What is the PM POSHAN scheme and who is eligible for it?",
        "ground_truth": (
            "PM POSHAN (Pradhan Mantri Poshan Shakti Nirman) is a centrally sponsored "
            "scheme that provides free hot cooked meals to students in government and "
            "government-aided primary schools. Children in Classes I to VIII studying "
            "in eligible schools receive nutritious mid-day meals on all school working days."
        ),
    },
    {
        "question": "What scholarships does AICTE offer to students in technical education?",
        "ground_truth": (
            "AICTE offers the Pragati Scholarship for girl students and the Saksham "
            "Scholarship for students with disabilities enrolled in AICTE-approved "
            "technical institutions. Both scholarships cover tuition fees and provide "
            "financial assistance for degree and diploma programmes."
        ),
    },
    {
        "question": "How can a faculty member apply for a UGC research grant?",
        "ground_truth": (
            "Faculty members can apply for UGC research grants through the UGC online "
            "e-portal by submitting a detailed research proposal. Applicants must hold "
            "a permanent position in a recognized university or college. Applications "
            "are reviewed by expert committees and funds are released in instalments."
        ),
    },
    {
        "question": "What are the benefits and features of the Swayam online learning platform?",
        "ground_truth": (
            "SWAYAM is a government MOOC platform offering free online courses from "
            "Class 9 to postgraduate level. All learners can access courses without fee; "
            "proctored exam certificates may require a nominal charge. Courses from top "
            "universities can earn UGC-recognised academic credits."
        ),
    },
    {
        "question": "What is the Diksha portal and how does it support teachers?",
        "ground_truth": (
            "DIKSHA (Digital Infrastructure for Knowledge Sharing) is a national "
            "platform providing teachers with curriculum-linked digital content, "
            "training modules, and QR-coded textbook integration across Indian languages. "
            "It helps teachers access lesson plans, assessments, and professional "
            "development resources online."
        ),
    },
    {
        "question": "How are NPTEL courses assessed and what certificates do students receive?",
        "ground_truth": (
            "NPTEL offers video lectures jointly by IITs and IISc. Assessment includes "
            "weekly online assignments and a proctored final exam at registered centres. "
            "Students who pass receive certificates that carry academic credit recognition "
            "at many institutes."
        ),
    },
    {
        "question": "What is the Vidyanjali initiative and what are its objectives?",
        "ground_truth": (
            "Vidyanjali is a school volunteer programme by the Ministry of Education "
            "that connects professionals, NRIs, and corporates with government schools. "
            "Volunteers contribute teaching assistance, infrastructure support, or "
            "assets to strengthen education quality in government schools."
        ),
    },
    {
        "question": "What AICTE guidelines exist for curriculum revision in technical institutions?",
        "ground_truth": (
            "AICTE issues periodic model curriculum guidelines mandating inclusion of "
            "emerging technologies, mandatory internships, project-based learning, and "
            "outcome-based education in undergraduate and postgraduate technical programmes. "
            "Institutions must update syllabi per these norms to maintain AICTE approval."
        ),
    },
    {
        "question": "What is the National Education Policy 2020 vision for higher education?",
        "ground_truth": (
            "NEP 2020 envisions holistic, multidisciplinary higher education with a GER "
            "target of 50 percent by 2035, flexible degree structures with multiple entry "
            "and exit options, Academic Credit Banks, vocational education integration, "
            "and emphasis on research, internationalisation, and governance reform."
        ),
    },
    {
        "question": "Who won the FIFA World Cup in 2022?",
        "ground_truth": (
            "I don't know based on the provided documents. This is outside the scope "
            "of the indexed government education documents."
        ),
    },
]
# ─────────────────────────────────────────────────────────────────────────────


def collect_results(dataset: list):
    from agents import RelevanceAgent, GeneratorAgent

    logger.info("Initialising pipeline agents…")
    retriever = RelevanceAgent()
    generator = GeneratorAgent()

    questions, ground_truths, answers, contexts_list = [], [], [], []

    for idx, case in enumerate(dataset, 1):
        q  = case["question"]
        gt = case["ground_truth"]
        logger.info(f"[{idx}/{len(dataset)}] {q[:80]}")

        docs = retriever.retrieve(q)
        ctx  = [d["content"] for d in docs] if docs else ["No relevant context found."]

        if docs:
            ans = generator.generate_answer(q, docs, query_id=f"eval_{idx}")
        else:
            ans = "The requested information is not available in the provided official documents."

        logger.info(f"  → Contexts: {len(ctx)} | Answer: {len(ans)} chars")

        questions.append(q)
        ground_truths.append(gt)
        answers.append(ans)
        contexts_list.append(ctx)
        time.sleep(0.3)

    return questions, ground_truths, answers, contexts_list


def run_ragas(questions, ground_truths, answers, contexts_list):
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
    from langchain_ollama import ChatOllama
    from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    hf_dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts_list,
        "ground_truth": ground_truths,
    })

    # ── Judge LLM: Ollama llama3.2 ────────────────────────────────────────────
    judge_llm = LangchainLLMWrapper(
        ChatOllama(
            model=LLM_MODEL_NAME,
            base_url=OLLAMA_BASE_URL,
            temperature=0.0,
            timeout=120,
        )
    )

    # ── Embeddings: FastEmbed (local, no HTTP hang) ───────────────────────────
    judge_emb = LangchainEmbeddingsWrapper(
        FastEmbedEmbeddings(model_name=EMBED_MODEL_NAME)
    )

    logger.info(
        f"\nRunning RAGAS evaluation — LLM: {LLM_MODEL_NAME}, "
        f"Embeddings: {EMBED_MODEL_NAME}"
    )
    logger.info("Computing 4 metrics × 10 questions — approx 5-10 min…\n")

    result = evaluate(
        dataset=hf_dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=judge_llm,
        embeddings=judge_emb,
    )

    df = result.to_pandas()

    def safe_mean(col):
        return round(float(df[col].mean()), 4) if col in df.columns else None

    summary = {
        "faithfulness":      safe_mean("faithfulness"),
        "answer_relevancy":  safe_mean("answer_relevancy"),
        "context_precision": safe_mean("context_precision"),
        "context_recall":    safe_mean("context_recall"),
    }
    per_question = df.to_dict(orient="records")
    return summary, per_question


def print_table(summary: dict):
    print("\n" + "═" * 60)
    print("  RAGAS PERFORMANCE METRICS — FINAL RESULTS")
    print("═" * 60)
    labels = {
        "faithfulness":      "Faithfulness",
        "answer_relevancy":  "Answer Relevancy",
        "context_precision": "Context Precision",
        "context_recall":    "Context Recall",
    }
    for key, label in labels.items():
        score = summary.get(key)
        if score is not None:
            bar = "█" * int(score * 20)
            print(f"  {label:<22}  {score:.4f}  {bar}")
        else:
            print(f"  {label:<22}  N/A")
    print("═" * 60 + "\n")


def main():
    logger.info("=" * 60)
    logger.info("Smart RAG — RAGAS Performance Evaluation")
    logger.info(f"LLM    : {LLM_MODEL_NAME} @ {OLLAMA_BASE_URL}")
    logger.info(f"Embeds : {EMBED_MODEL_NAME} (FastEmbed local)")
    logger.info("=" * 60)

    # Phase 1 — collect pipeline outputs
    questions, ground_truths, answers, contexts_list = collect_results(TEST_DATASET)
    logger.info(f"\nPipeline phase complete — {len(questions)} queries processed.")

    # Intermediate save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"questions": questions, "answers": answers,
             "contexts": contexts_list, "ground_truths": ground_truths},
            f, indent=2, default=str,
        )
    logger.info(f"Intermediate results saved to {OUTPUT_PATH}")

    # Phase 2 — RAGAS evaluation
    summary, per_question = run_ragas(questions, ground_truths, answers, contexts_list)

    # Full save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"summary": summary, "per_question": per_question,
             "questions": questions, "answers": answers,
             "contexts": contexts_list, "ground_truths": ground_truths},
            f, indent=2, default=str,
        )

    print_table(summary)
    logger.info(f"Full results saved to {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    main()
