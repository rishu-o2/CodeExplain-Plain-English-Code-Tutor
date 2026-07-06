# =============================================================================
# utils/prompts.py — Prompt Templates for Gemini AI
# =============================================================================
# CENTRAL TEMPLATE DIRECTORY
# This file stores all prompt generator functions used to instruct Google Gemini.
# Every prompt specifies:
#   - Context (programming language, source code)
#   - Task (explaining, complexity, bugs, quiz, etc.)
#   - Required JSON output schema to ensure API compliance
#
# Constraints:
#   - Return ONLY valid JSON.
#   - Do NOT include Markdown.
#   - Do NOT wrap the JSON inside code fences.
#   - Do NOT include explanations before or after the JSON.
#   - Do NOT include additional notes.
#   - The response must be directly parseable using Python's json.loads().
# =============================================================================

def get_summary_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to explain code in plain English and rate its difficulty.

    Args:
        code: The source code snippet.
        language: The programming language (or Auto Detect).

    Returns:
        Formatted prompt string.
    """
    return f"""
You are an expert programming tutor who explains complex code concepts in simple, plain English without jargon.
Analyze the following {language} code snippet:

```
{code}
```

Instructions:
1. Explain what this code does at a high level. Use clear, pedagogical, and beginner-friendly language. Make the explanation logical and thorough.
2. Determine the educational difficulty level of this code (Beginner, Intermediate, or Advanced).

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "summary": "Detailed plain-English summary of the code's purpose, design, logic flow, and overall utility.",
  "difficulty": "Beginner | Intermediate | Advanced"
}}
"""


def get_line_by_line_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to get a line-by-line breakdown of the code.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
You are an expert programming tutor. Explain the following {language} code snippet line-by-line:

```
{code}
```

Instructions:
1. Break down the code systematically.
2. For each meaningful line or logical block, provide a clear explanation.
3. Keep the explanations highly pedagogical, explaining *why* a construct is used (e.g. why recursion, why a particular conditional test, why a specific API call).

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "line_by_line": [
    {{
      "line_number": 1,
      "code_line": "exact line of code here",
      "explanation": "pedagogical, plain-English explanation for this specific line"
    }}
  ]
}}
"""


def get_complexity_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to evaluate time and space complexity, readability, and nesting.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
Analyze the algorithmic complexity and code metrics of the following {language} code snippet:

```
{code}
```

Instructions:
1. Determine the Time Complexity using Big-O notation (e.g., O(1), O(log n), O(n), O(n log n), O(n^2), O(2^n)).
2. Determine the Space Complexity using Big-O notation (e.g., O(1), O(n), O(n^2)).
3. Calculate the maximum Nesting Depth (the maximum level of nested conditionals, loops, or blocks).
4. Evaluate the Readability Score (an integer from 1 to 10 based on structure, naming, comments, and style).
Provide highly accurate, standard academic complexity estimates.

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "time": "O(1) | O(log n) | O(n) | O(n log n) | O(n^2) | O(2^n) | etc.",
  "space": "O(1) | O(n) | O(n^2) | etc.",
  "nesting_depth": 0,
  "readability": 0
}}
"""


def get_improvements_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to suggest idiomatic improvements or refactoring suggestions.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
You are a senior developer conducting a rigorous code review.
Provide up to 3 refactoring or optimization recommendations for the following {language} code snippet:

```
{code}
```

Instructions:
1. Focus on idiomatic practices (e.g., Pythonic style, Java design patterns, C++ core guidelines, modern JavaScript).
2. Offer tips targeting performance, safety, readability, or modern language standards.

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "improvements": [
    "Tip 1: Clear, actionable explanation of the improvement, what change to make, and its benefits",
    "Tip 2: Clear, actionable explanation of the improvement, what change to make, and its benefits",
    "Tip 3: Clear, actionable explanation of the improvement, what change to make, and its benefits"
  ]
}}
"""


def get_bugs_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to detect bugs, logic errors, or edge-case failures.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
Perform a security and logic audit on the following {language} code snippet:

```
{code}
```

Instructions:
1. Identify logic errors, syntax mistakes, anti-patterns, infinite loops, memory leaks, unhandled exceptions, or severe edge-case failures.
2. Provide severity levels: High, Medium, or Low.
3. Outline a fix code snippet for each issue.
4. If the code is fully correct, safe, and bug-free, return an empty list for "bugs".

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "bugs": [
    {{
      "severity": "High | Medium | Low",
      "description": "Thorough explanation of the issue, why it occurs, and the impact.",
      "fix": "Corrected code snippet implementing the fix."
    }}
  ]
}}
"""


def get_quiz_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to generate comprehension quiz questions.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
Design a highly educational interactive quiz consisting of 3 multiple-choice questions to test deep comprehension of the following {language} code snippet:

```
{code}
```

Instructions:
1. Focus on code behavior, outputs of execution, state transitions, variable roles, or base case criteria.
2. Provide 4 distinct options (A, B, C, D) for each question.
3. Identify the correct answer (matching the exact option text).
4. Provide a detailed explanation explaining both why the correct answer is correct and why other key choices are incorrect.

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "quiz": [
    {{
      "question": "A clear, conceptual question assessing comprehension.",
      "options": [
        "A) Option A description",
        "B) Option B description",
        "C) Option C description",
        "D) Option D description"
      ],
      "answer": "Correct option text exactly as formatted in options, e.g., 'B) Option B description'",
      "explanation": "Detailed explanation of correct answer logic and choice analysis."
    }}
  ]
}}
"""


def get_learning_tips_prompt(code: str, language: str) -> str:
    """
    Generate a prompt to suggest study guides, practice exercises, and next steps.

    Args:
        code: The source code snippet.
        language: The programming language.

    Returns:
        Formatted prompt string.
    """
    return f"""
Analyze the underlying algorithms, paradigms, language constructs, and design patterns used in this {language} code snippet:

```
{code}
```

Instructions:
1. Provide a comprehensive syllabus of next steps, structured practice tasks, concepts to revise, and advanced topics.
2. Group suggestions under standard educational categories.

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "learning_tips": [
    "Concept definition / review tip (e.g. Recursion - explaining call stack behaviour)",
    "Related study topic (e.g. Dynamic Programming - memoization/tabulation techniques)",
    "Suggested coding practice challenge (e.g. Iterative rewrite of the function)",
    "Advanced conceptual recommendation (e.g. Divide and conquer paradigm mechanics)"
  ]
}}
"""
