"""
Basic example of using GuidedCapture.
"""

import os
from openai import OpenAI
from guided_capture import GuidedCapture

def main():
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    
    client = OpenAI(api_key=api_key)

    # Create a new interview session
    capture = GuidedCapture(
        topic="Company Vision",
        output_format_description="A concise and inspiring company mission statement (1-3 sentences)",
        llm_client=client,
        num_questions=5,
        model="gpt-4o"  # Use a capable model
    )

    try:
        # Get questions
        print("\nGenerating interview questions...")
        questions = capture.get_questions()
        print("\nPlease answer the following questions:")

        # Collect answers
        for i, question in enumerate(questions, 1):
            print(f"\n{i}. {question}")
            answer = input("Your answer: ")
            capture.submit_answer(question, answer)

        # Process answers and get final output
        print("\nSynthesizing mission statement...")
        final_output = capture.process_answers()

        print("\n--- Generated Mission Statement ---")
        print(final_output)

        # Optionally save state
        state = capture.get_state()
        import json
        with open("mission_session.json", "w") as f:
            json.dump(state, f, indent=2)
        print("\nSession state saved to mission_session.json")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main() 