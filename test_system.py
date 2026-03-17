from main import RAGPipeline
import colorama
from colorama import Fore

colorama.init(autoreset=True)

def test_system():
    pipeline = RAGPipeline()
    
    test_queries = [
        "Method of Resolving ties (For Degree Level)",
        "What schemes are available for AICTE?",
        "What is the funding for PMJVK?",
        "Tell me about the National Merit Scholarship Scheme",
        "What is the capital of Mars? (Testing irrelevant query)"
    ]

    print(f"{Fore.GREEN}Starting Automated Tests...\n")

    for query in test_queries:
        print(f"Testing Query: {query}")
        result = pipeline.process_query(query)
        print(result)
        print("-" * 60)

if __name__ == "__main__":
    test_system()
