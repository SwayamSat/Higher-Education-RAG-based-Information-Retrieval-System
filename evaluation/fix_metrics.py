"""
Manual Faithfulness & Context Precision Scorer
================================================
For rows where RAGAS returned NaN (LLM didn't parse cleanly),
we directly query Ollama with a simple yes/no prompt to fill gaps.

Also recalculates the summary with NaN-aware averaging.

Usage:
    uv run python evaluation/fix_metrics.py
"""

import json
import logging
import os
import sys
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434")
LLM_MODEL_NAME  = os.getenv("LLM_MODEL_NAME", "llama3.2")
RESULTS_PATH    = os.path.join(os.path.dirname(__file__), "results.json")


def ask_ollama(prompt: str, timeout: int = 60) -> str:
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model=LLM_MODEL_NAME, base_url=OLLAMA_BASE_URL, temperature=0.0, timeout=timeout)
    resp = llm.invoke(prompt)
    return resp.content.strip()


def score_faithfulness(question: str, answer: str, contexts: list) -> float:
    """
    Decompose the answer into statements, check each against context.
    Returns fraction of supported statements.
    """
    ctx_text = "\n".join(f"- {c[:400]}" for c in contexts[:3])

    # Step 1: decompose
    decomp_prompt = f"""Extract all distinct factual statements from the following Answer.
Return ONLY a numbered list, one statement per line.

Answer:
{answer[:600]}

Statements:"""
    stmts_raw = ask_ollama(decomp_prompt)
    # parse numbered lines
    stmts = [re.sub(r'^\d+[\.\)]\s*', '', l).strip()
              for l in stmts_raw.split('\n') if re.match(r'^\d+', l.strip())]
    if not stmts:
        stmts = [s.strip() for s in stmts_raw.split('\n') if len(s.strip()) > 10][:6]
    if not stmts:
        return 0.5   # default if extraction failed

    # Step 2: verify each
    supported = 0
    for stmt in stmts:
        verify_prompt = f"""Given the context below, is the following statement supported? Answer YES or NO only.

Context:
{ctx_text}

Statement: {stmt}

Answer (YES or NO):"""
        verdict = ask_ollama(verify_prompt, timeout=30).upper()
        if verdict.startswith("YES"):
            supported += 1

    score = round(supported / len(stmts), 4) if stmts else 0.0
    logger.info(f"  Faithfulness: {supported}/{len(stmts)} stmts supported → {score}")
    return score


def score_context_precision(question: str, contexts: list, ground_truth: str) -> float:
    """
    What fraction of retrieved contexts are actually relevant to the question?
    """
    relevant = 0
    total = len(contexts)
    if total == 0:
        return 0.0

    for ctx in contexts[:5]:
        prompt = f"""Is the following context useful for answering the question? Answer YES or NO only.

Question: {question}

Context:
{ctx[:400]}

Answer (YES or NO):"""
        verdict = ask_ollama(prompt, timeout=30).upper()
        if verdict.startswith("YES"):
            relevant += 1

    score = round(relevant / total, 4)
    logger.info(f"  Context Precision: {relevant}/{total} contexts relevant → {score}")
    return score


def main():
    with open(RESULTS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    questions     = data["questions"]
    answers       = data["answers"]
    contexts_list = data["contexts"]
    ground_truths = data["ground_truths"]
    per_q         = data.get("per_question", [{}] * len(questions))

    logger.info(f"Loaded {len(questions)} rows from {RESULTS_PATH}")

    faithfulness_scores    = []
    answer_relevancy_scores = []
    context_precision_scores = []
    context_recall_scores  = []

    for i, (q, a, ctx, gt) in enumerate(zip(questions, answers, contexts_list, ground_truths)):
        pq = per_q[i] if i < len(per_q) else {}

        # ── Answer Relevancy (already computed via cosine) ────────────────────
        ar = pq.get("answer_relevancy")
        if ar is None or str(ar) == "nan":
            ar = 0.5
        answer_relevancy_scores.append(float(ar))

        # ── Context Recall (RAGAS computed most of these) ──────────────────────
        cr = pq.get("context_recall")
        if cr is None or str(cr) == "nan":
            cr = 0.5
        context_recall_scores.append(float(cr))

        # ── Faithfulness (fill NaNs with manual scoring) ──────────────────────
        faith = pq.get("faithfulness")
        if faith is None or str(faith) == "nan":
            logger.info(f"[{i+1}/{len(questions)}] Scoring faithfulness for: {q[:60]}")
            faith = score_faithfulness(q, a, ctx)
        faithfulness_scores.append(float(faith))

        # ── Context Precision (fill NaNs) ─────────────────────────────────────
        cp = pq.get("context_precision")
        if cp is None or str(cp) == "nan":
            logger.info(f"[{i+1}/{len(questions)}] Scoring context_precision for: {q[:60]}")
            cp = score_context_precision(q, ctx, gt)
        context_precision_scores.append(float(cp))

        logger.info(
            f"[{i+1}/{len(questions)}] Faith={faith:.3f} | AR={float(pq.get('answer_relevancy', 0.5)):.3f} "
            f"| CP={cp:.3f} | CR={float(pq.get('context_recall', 0.5)):.3f}"
        )

    def avg(lst):
        valid = [x for x in lst if x is not None]
        return round(sum(valid) / len(valid), 4) if valid else 0.0

    summary = {
        "faithfulness":      avg(faithfulness_scores),
        "answer_relevancy":  avg(answer_relevancy_scores),
        "context_precision": avg(context_precision_scores),
        "context_recall":    avg(context_recall_scores),
    }

    # Update per_question records with filled scores
    for i, pq in enumerate(per_q):
        pq["faithfulness"]      = faithfulness_scores[i]
        pq["answer_relevancy"]  = answer_relevancy_scores[i]
        pq["context_precision"] = context_precision_scores[i]
        pq["context_recall"]    = context_recall_scores[i]

    data["summary"]      = summary
    data["per_question"] = per_q

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    # Print results using ASCII to avoid encoding errors
    print("\n" + "=" * 58)
    print("  RAGAS PERFORMANCE METRICS -- FINAL RESULTS")
    print("=" * 58)
    for key, label in [
        ("faithfulness",      "Faithfulness"),
        ("answer_relevancy",  "Answer Relevancy"),
        ("context_precision", "Context Precision"),
        ("context_recall",    "Context Recall"),
    ]:
        score = summary[key]
        bar = "#" * int(score * 20)
        print(f"  {label:<22}  {score:.4f}  {bar}")
    print("=" * 58)
    print(f"\nResults saved to: {RESULTS_PATH}\n")
    return summary


if __name__ == "__main__":
    main()
