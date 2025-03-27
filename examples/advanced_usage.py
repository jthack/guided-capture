"""
Advanced example of using GuidedCapture with bulk answer submission and state management.
"""

import os
import json
from openai import OpenAI
from guided_capture import GuidedCapture

def save_state(capture: GuidedCapture, filename: str):
    """Helper function to save session state."""
    state = capture.get_state()
    with open(filename, "w") as f:
        json.dump(state, f, indent=2)
    print(f"\nSession state saved to {filename}")

def load_state(filename: str, llm_client) -> GuidedCapture:
    """Helper function to load session state."""
    with open(filename, "r") as f:
        state = json.load(f)
    return GuidedCapture.load_state(state, llm_client)

def main():
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    
    client = OpenAI(api_key=api_key)

    # Example 1: Product Feature Brainstorming
    print("\n=== Example 1: Product Feature Brainstorming ===")
    feature_capture = GuidedCapture(
        topic="Brainstorming core features for a mobile app that helps users track personal habits",
        output_format_description="A bulleted list of 5-7 key feature ideas with brief descriptions",
        llm_client=client,
        num_questions=6
    )

    try:
        # Get questions
        print("\nGenerating questions about product features...")
        questions = feature_capture.get_questions()

        # Example: Submit answers in bulk
        # In a real application, these would come from user input, a form, or another source
        dummy_answers = {
            questions[0]: "Make it easy to add new habits and track daily completion",
            questions[1]: "Users need reminders and motivation, maybe streaks or points",
            questions[2]: "Visual progress charts are important",
            questions[3]: "Perhaps social features, like sharing progress with friends (optional)",
            questions[4]: "Keep the interface simple and quick to use",
            questions[5]: "Integration with calendars might be useful"
        }

        print("\nSubmitting answers in bulk...")
        feature_capture.submit_answers_bulk(dummy_answers)

        # Process answers
        print("\nSynthesizing feature ideas...")
        final_features = feature_capture.process_answers()

        print("\n--- Generated Feature Ideas ---")
        print(final_features)

        # Save state
        save_state(feature_capture, "feature_session.json")

    except Exception as e:
        print(f"\nAn error occurred during feature brainstorming: {e}")

    # Example 2: Resume State Management
    print("\n=== Example 2: Resume State Management ===")
    try:
        # Load the previously saved state
        print("\nLoading saved session state...")
        resumed_capture = load_state("feature_session.json", client)

        # Verify the state was loaded correctly
        print("\nVerifying loaded state:")
        print(f"Topic: {resumed_capture.topic}")
        print(f"Number of questions: {len(resumed_capture.questions)}")
        print(f"Number of answers: {len(resumed_capture.answers)}")
        print(f"Final output: {resumed_capture.final_output}")

        # Example: Add a new answer to an existing question
        if resumed_capture.questions:
            question = resumed_capture.questions[0]
            print(f"\nAdding new answer for: {question}")
            new_answer = "Updated answer with more details"
            resumed_capture.submit_answer(question, new_answer)
            print(f"Updated answer: {resumed_capture.answers[question]}")

            # Process with updated answer
            print("\nSynthesizing with updated answer...")
            updated_output = resumed_capture.process_answers()
            print("\n--- Updated Feature Ideas ---")
            print(updated_output)

    except Exception as e:
        print(f"\nAn error occurred during state management: {e}")

if __name__ == "__main__":
    main() 