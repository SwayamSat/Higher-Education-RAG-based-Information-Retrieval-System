import colorama
from colorama import Fore, Style
from agents import RelevanceAgent, GeneratorAgent, FactCheckAgent

colorama.init(autoreset=True)

class RAGPipeline:
    def __init__(self):
        self.retriever = RelevanceAgent()
        self.generator = GeneratorAgent()
        self.verifier = FactCheckAgent()

    def process_query(self, query):
        print(f"\n{Fore.MAGENTA}{'='*50}")
        print(f"{Fore.MAGENTA}Processing Query: {query}")
        print(f"{Fore.MAGENTA}{'='*50}\n")

        # Step 1: Retrieval
        relevant_docs = self.retriever.retrieve(query)
        if not relevant_docs:
            return self.format_output("The requested information is not available in the provided official documents.", "N/A", "Low", {"status": "N/A", "reason": "No documents found"})

        # Step 2: Generation
        # Step 2: Generation
        initial_answer = self.generator.generate_answer(query, relevant_docs)
        answer = initial_answer

        # Step 3: Verification
        verification_result = self.verifier.verify(query, answer, relevant_docs)
        
        # Step 4: Self-Correction Loop (Simple Implementation)
        if verification_result["status"] != "Verified":
            print(f"{Fore.RED}Verification Failed: {verification_result['reason']}")
            print(f"{Fore.YELLOW}Attempting Self-Correction...")
            
            # Simple correction: Try to generate again with stricter instruction
            # In a full system, you might refine the query or fetch more docs
            new_query = query + " (Ensure answer is strictly based on context)"
            answer = self.generator.generate_answer(new_query, relevant_docs)
            
            # Re-verify
            verification_result = self.verifier.verify(new_query, answer, relevant_docs)
            if verification_result["status"] != "Verified":
                answer = "The requested information could not be verified from official documents."
                confidence = "Low"
            else:
                confidence = "Medium" # Corrected answers might be less confident
        else:
            confidence = "High"

        # Extract Sources
        sources = set()
        for doc in relevant_docs:
            sources.add(doc['metadata']['source'])
        source_str = ", ".join(sources) if sources else "N/A"

        # Extract Sources
        sources = set()
        for doc in relevant_docs:
            sources.add(doc['metadata']['source'])
        source_str = ", ".join(sources) if sources else "N/A"

        return self.format_output(answer, source_str, confidence, verification_result, generated_answer=initial_answer)

    def format_output(self, answer, source, confidence, verification_result=None, generated_answer=None):
        output = f"""
{Fore.CYAN}Final Answer:{Style.RESET_ALL}
{answer}
"""
        if generated_answer and generated_answer != answer:
            output += f"""
{Fore.MAGENTA}Generated Answer (Before Verification):{Style.RESET_ALL}
{generated_answer}
"""

        output += f"""
{Fore.CYAN}Source:{Style.RESET_ALL}
{source}

{Fore.CYAN}Confidence:{Style.RESET_ALL}
{confidence}
"""
        if verification_result:
             output += f"""
{Fore.YELLOW}Verification Status:{Style.RESET_ALL}
{verification_result['status']}

{Fore.YELLOW}Verification Reason:{Style.RESET_ALL}
{verification_result['reason']}
"""
        return output

def main():
    print(f"{Fore.GREEN}Smart Retrieval of Education Schemes (RAG System)")
    print(f"{Fore.GREEN}Type 'exit' to quit.\n")
    
    pipeline = RAGPipeline()
    
    while True:
        try:
            query = input(f"{Fore.BLUE}\nEnter your query: {Style.RESET_ALL}")
            if query.lower() in ['exit', 'quit']:
                break
            
            if not query.strip():
                continue
                
            response = pipeline.process_query(query)
            print(response)
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}")

if __name__ == "__main__":
    main()
