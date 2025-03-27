"""
Core implementation of the GuidedCapture library.
"""

import json
from typing import List, Dict, Optional, Any, Union

class GuidedCapture:
    """
    Manages a guided interview process to capture user context and synthesize output.
    """

    def __init__(
        self,
        topic: str,
        output_format_description: str,
        llm_client: Any, # Pass an initialized LLM client (OpenAI, Anthropic, etc.)
        num_questions: Optional[int] = 5,
        question_generation_prompt_template: Optional[str] = None,
        synthesis_prompt_template: Optional[str] = None,
        model: str = "gpt-3.5-turbo", # Or your preferred model
    ):
        """
        Initializes the GuidedCapture session.

        Args:
            topic: The central theme or goal of the interview (e.g., "Company Vision", "Social Media Post Idea").
            output_format_description: A description of the desired final output
                                       (e.g., "A concise company mission statement",
                                        "A bulleted list of features for a new app",
                                        "A draft social media post").
            llm_client: An initialized client for interacting with an LLM.
            num_questions: Approximate number of questions to generate.
            question_generation_prompt_template: Optional custom prompt template for generating questions.
            synthesis_prompt_template: Optional custom prompt template for synthesizing the final output.
            model: The LLM model to use.
        """
        if not topic or not output_format_description:
            raise ValueError("Both 'topic' and 'output_format_description' are required.")
        if not hasattr(llm_client, 'chat') and not hasattr(llm_client.chat, 'completions'): # Basic check for OpenAI-like client
             raise TypeError("llm_client does not appear to be a compatible LLM client.")

        self.topic = topic
        self.output_format_description = output_format_description
        self.num_questions = num_questions
        self.llm_client = llm_client
        self.model = model

        self.question_generation_prompt_template = question_generation_prompt_template or self._default_question_prompt()
        self.synthesis_prompt_template = synthesis_prompt_template or self._default_synthesis_prompt()

        self.questions: List[str] = []
        self.answers: Dict[str, str] = {} # Using question text as key for simplicity
        self._questions_generated = False
        self._synthesis_complete = False
        self.final_output: Optional[str] = None

    def _default_question_prompt(self) -> str:
        return """
        You are an expert interviewer helping gather information.
        The main topic or goal is: "{topic}"
        The desired final output based on the interview answers is: "{output_format_description}"

        Generate approximately {num_questions} insightful and open-ended questions that will help elicit the necessary information from a user to achieve this goal.
        Focus on understanding the core ideas, motivations, challenges, and key details relevant to the topic and desired output.
        Avoid simple yes/no questions.

        Output the questions as a JSON list of strings. Example: ["Question 1?", "Question 2?", "Question 3?"]
        JSON Questions:
        """

    def _default_synthesis_prompt(self) -> str:
        return """
        You are an expert synthesizer of information.
        You have conducted an interview based on the topic: "{topic}"
        The goal was to produce the following output: "{output_format_description}"

        Here are the questions asked and the answers received:
        {qa_pairs}

        Based *only* on the provided questions and answers, synthesize the information and generate the desired output as described.
        Adhere strictly to the requested output format. If the answers are insufficient, state that clearly instead of inventing information. Only do this when there is basically no information to work with. For the most part, you should attempt to complete the output format.

        Final Synthesized Output:
        """

    def _call_llm(self, prompt: str) -> str:
        """Helper function to interact with the LLM."""
        try:
            # Adapt this based on the specific LLM client library method
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7, # Adjust as needed
            )
            # Access the response content correctly based on your client library
            content = response.choices[0].message.content
            return content.strip()
        except Exception as e:
            print(f"Error calling LLM: {e}")
            # Consider more robust error handling/logging
            raise

    def generate_questions(self) -> List[str]:
        """
        Generates the interview questions using the LLM.
        """
        if self._questions_generated:
            return self.questions

        prompt = self.question_generation_prompt_template.format(
            topic=self.topic,
            output_format_description=self.output_format_description,
            num_questions=self.num_questions
        )

        raw_response = self._call_llm(prompt)

        try:
            # Attempt to parse the JSON list of questions
            # Find the start of the JSON list
            json_start = raw_response.find('[')
            json_end = raw_response.rfind(']') + 1
            if json_start != -1 and json_end != 0:
                json_str = raw_response[json_start:json_end]
                self.questions = json.loads(json_str)
                if not isinstance(self.questions, list) or not all(isinstance(q, str) for q in self.questions):
                    raise ValueError("LLM did not return a valid JSON list of strings.")
            else:
                 # Fallback: try splitting by newline if JSON parsing fails
                 print("Warning: LLM response was not valid JSON. Attempting newline split.")
                 self.questions = [q.strip() for q in raw_response.split('\n') if q.strip()]

            if not self.questions:
                 raise ValueError("LLM failed to generate any questions.")

            self._questions_generated = True
            # Initialize answers dict with empty strings
            self.answers = {q: "" for q in self.questions}
            return self.questions
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing questions from LLM response: {e}")
            print(f"Raw response was:\n{raw_response}")
            # Handle error - maybe retry, raise exception, or return empty list
            self.questions = []
            self.answers = {}
            raise ValueError(f"Failed to parse questions from LLM. Raw response: {raw_response}") from e

    def get_questions(self) -> List[str]:
        """
        Returns the list of generated questions. Generates them if not already done.
        """
        if not self._questions_generated:
            self.generate_questions()
        return self.questions

    def submit_answer(self, question: str, answer: str):
        """
        Allows the calling application to submit an answer for a specific question.

        Args:
            question: The exact text of the question being answered.
            answer: The user's answer.
        """
        if not self._questions_generated:
            raise RuntimeError("Questions have not been generated yet. Call generate_questions() first.")
        if question not in self.answers:
            # Maybe allow adding ad-hoc questions/answers? For now, strict.
            raise ValueError(f"Unknown question: '{question}'. Must be one of the generated questions.")

        self.answers[question] = answer
        self._synthesis_complete = False # New answers invalidate previous synthesis
        self.final_output = None

    def submit_answers_bulk(self, answers_dict: Dict[str, str]):
        """Submits multiple answers at once."""
        if not self._questions_generated:
            raise RuntimeError("Questions have not been generated yet. Call generate_questions() first.")
        for question, answer in answers_dict.items():
            if question in self.answers:
                self.answers[question] = answer
            else:
                print(f"Warning: Skipping unknown question during bulk submit: '{question}'")
        self._synthesis_complete = False
        self.final_output = None

    def get_missing_questions(self) -> List[str]:
        """Returns a list of questions that haven't received an answer yet."""
        if not self._questions_generated:
             return []
        return [q for q, a in self.answers.items() if not a]

    def process_answers(self) -> str:
        """
        Synthesizes the final output based on collected answers using the LLM.
        """
        if self._synthesis_complete and self.final_output is not None:
            return self.final_output

        if not self._questions_generated:
            raise RuntimeError("Cannot process answers before questions are generated.")

        missing = self.get_missing_questions()
        if missing:
            # Or raise an error, depending on desired behavior
            print(f"Warning: Cannot process yet. Missing answers for: {missing}")
            # Decide: proceed anyway, or force completion? Let's allow proceeding but warn.
            # raise ValueError(f"Cannot process. Missing answers for: {missing}")

        qa_pairs_text = "\n".join([f"Q: {q}\nA: {a}" for q, a in self.answers.items() if a]) # Only include answered questions

        if not qa_pairs_text:
             raise ValueError("No answers have been submitted yet.")

        prompt = self.synthesis_prompt_template.format(
            topic=self.topic,
            output_format_description=self.output_format_description,
            qa_pairs=qa_pairs_text
        )

        self.final_output = self._call_llm(prompt)
        self._synthesis_complete = True
        return self.final_output

    def get_state(self) -> Dict[str, Any]:
         """Returns the current state for serialization."""
         return {
              "topic": self.topic,
              "output_format_description": self.output_format_description,
              "num_questions": self.num_questions,
              "model": self.model,
              "questions": self.questions,
              "answers": self.answers,
              "_questions_generated": self._questions_generated,
              "_synthesis_complete": self._synthesis_complete,
              "final_output": self.final_output,
              # Note: We don't serialize templates or the llm_client itself easily
         }

    @classmethod
    def load_state(cls, state: Dict[str, Any], llm_client: Any) -> 'GuidedCapture':
         """Rehydrates an instance from a saved state."""
         instance = cls(
              topic=state['topic'],
              output_format_description=state['output_format_description'],
              llm_client=llm_client,
              num_questions=state.get('num_questions', 5), # Provide default if missing
              model=state.get('model', "gpt-3.5-turbo")
         )
         instance.questions = state.get('questions', [])
         instance.answers = state.get('answers', {})
         instance._questions_generated = state.get('_questions_generated', False)
         instance._synthesis_complete = state.get('_synthesis_complete', False)
         instance.final_output = state.get('final_output', None)
         # Ensure answers dict keys match questions if loaded separately
         if instance._questions_generated and not instance.answers:
             instance.answers = {q: "" for q in instance.questions}
         elif instance.answers and instance.questions:
              # Ensure all current questions exist as keys in answers
              for q in instance.questions:
                   if q not in instance.answers:
                        instance.answers[q] = ""
         return instance 