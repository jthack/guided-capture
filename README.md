# GuidedCapture

<p align="center">
  <img src="assets/guided-capture-bot.png" alt="GuidedCapture Bot" width="800"/>
</p>

An AI-powered library for conducting structured interviews and synthesizing responses into desired output formats.

## Overview

GuidedCapture is a flexible library that helps you conduct goal-oriented interviews using Large Language Models (LLMs). It generates relevant questions based on your objectives and synthesizes responses into your desired output format.

### Key Features

- **Goal-Oriented Interviewing**: Start with a clear topic and desired output format
- **LLM-Powered Question Generation**: Automatically generates relevant, probing questions
- **UI-Agnostic Design**: Works with any interface (CLI, web, mobile, etc.)
- **Flexible Answer Collection**: Submit answers progressively or in bulk
- **Intelligent Synthesis**: Processes Q&A pairs into your desired output format
- **State Management**: Save and resume interview sessions
- **Multiple LLM Support**: Works with various LLM providers (OpenAI, Anthropic, etc.)

## Installation

```bash
pip install guided-capture
```

## Quick Start

```python
from openai import OpenAI
from guided_capture import GuidedCapture

# Initialize your LLM client
client = OpenAI(api_key="your-api-key")

# Create a new interview session
capture = GuidedCapture(
    topic="Company Vision",
    output_format_description="A concise company mission statement",
    llm_client=client
)

# Get questions
questions = capture.get_questions()

# Collect answers (example with CLI)
for question in questions:
    print(f"\n{question}")
    answer = input("Your answer: ")
    capture.submit_answer(question, answer)

# Get final output
result = capture.process_answers()
print("\nFinal Output:", result)
```

## Advanced Usage

### Bulk Answer Submission

```python
# Submit multiple answers at once
answers = {
    "What is your company's main goal?": "To revolutionize AI accessibility",
    "Who is your target audience?": "Small businesses and startups",
    # ... more answers
}
capture.submit_answers_bulk(answers)
```

### State Management

```python
# Save session state
state = capture.get_state()
import json
with open("session.json", "w") as f:
    json.dump(state, f)

# Load session state
with open("session.json", "r") as f:
    state = json.load(f)
capture = GuidedCapture.load_state(state, llm_client)
```

### Custom Prompts

```python
capture = GuidedCapture(
    topic="Product Features",
    output_format_description="A list of key features",
    llm_client=client,
    question_generation_prompt_template="Custom prompt for questions...",
    synthesis_prompt_template="Custom prompt for synthesis..."
)
```

## Requirements

- Python 3.7+
- OpenAI API key (or other LLM provider credentials)
- Required packages:
  - openai (or other LLM client libraries)
  - typing (included in Python 3.5+)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details
