# =============================================================================
# utils/gemini_client.py — Google Gemini API Client Wrapper
# =============================================================================
# Exposes a single public method to request a comprehensive code analysis
# from Gemini in a single prompt execution.
#
# Model Configuration:
#   - Upgraded to gemini-2.5-flash.
#   - temperature: 0.2 to encourage highly deterministic JSON generation.
#
# Authentication:
#   - Reads GEMINI_API_KEY environment variable.
#   - Gracefully handles missing credentials with clear errors.
#
# Performance Optimization:
#   - Reduces active calls from 7 separate queries to 1 unified payload,
#     cutting latency, cost, token counts, and improving consistency.
# =============================================================================

from __future__ import annotations

import os
import json
import logging
from typing import Any
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# Setup module logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini_client")

# Default model version used for tutor tasks (Upgraded to 2.5-flash)
MODEL_NAME = "gemini-2.5-flash"


def _get_generative_model() -> genai.GenerativeModel:
    """
    Initialise the Google GenAI SDK and return a model instance.

    Reads from the environment variable GEMINI_API_KEY.

    Raises:
        ValueError: If the API key is missing.
        RuntimeError: If initialisation or model retrieval fails.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        raise ValueError(
            "Gemini API Key is not set. Please add GEMINI_API_KEY to your .env file."
        )

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(MODEL_NAME)
    except Exception as e:
        logger.error(f"Failed to configure or initialize Gemini model: {e}")
        raise RuntimeError(f"Failed to initialize Gemini API client: {e}") from e


def _get_complete_analysis_prompt(code: str, language: str) -> str:
    """
    Generate the unified single-request prompt instructing Gemini to analyze the code
    and return all details in a single JSON response.
    """
    return f"""
You are an expert developer, algorithm analyst, and programming tutor.
Analyze the following {language} code snippet:

```
{code}
```

Instructions:
1. Perform a complete tutorial analysis on this snippet.
2. Return all results inside ONE structured JSON response. Do not perform multiple separate answers.
3. Keep explanations clear, beginner-friendly, and educational.

Your JSON response must contain exactly these 8 keys:
- "summary": A detailed plain-English high-level overview explaining the purpose and utility of this code.
- "difficulty": Overall difficulty tier of the snippet ("Beginner", "Intermediate", or "Advanced").
- "line_by_line": A list of breakdown objects for all meaningful instructions. Each element must contain:
  - "label": e.g., "Line 1", "Line 2", etc.
  - "code": The exact instruction text.
  - "explanation": Plain-English explanation explaining what the instruction does.
- "complexity": Algorithmic metric evaluation:
  - "time": Big-O time complexity (e.g. O(1), O(log n), O(n), O(n log n), O(n^2), O(2^n)).
  - "space": Big-O space complexity (e.g. O(1), O(n)).
  - "readability": Readability score (integer from 1 to 10).
  - "nesting_depth": Maximum nesting block depth (integer).
- "improvements": An array of up to 3 refactoring or optimization tips.
- "bugs": A list of logic mistakes, infinite loops, security issues, or edge cases. Each element must contain:
  - "severity": "High | Medium | Low"
  - "description": Detailed problem summary.
  - "fix": Corrected code instruction.
- "quiz": 3 comprehension questions testing this code. Each element must contain:
  - "question": Question text.
  - "options": An array of 4 unique options (A, B, C, D).
  - "answer": Correct option text exactly as formatted (e.g. "B) option text").
  - "explanation": Pedagogical correct choice breakdown.
- "learning_tips": General recommendations, concepts to revise, practice exercises, and next study steps.

Return ONLY valid JSON.
Do NOT include Markdown.
Do NOT wrap the JSON inside code fences.
Do NOT include explanations before or after the JSON.
Do NOT include additional notes.
The response must be directly parseable using Python's json.loads().

Expected JSON schema:
{{
  "summary": "detailed explanation of code",
  "difficulty": "Beginner | Intermediate | Advanced",
  "line_by_line": [
    {{
      "label": "Line 1",
      "code": "def func():",
      "explanation": "explanation"
    }}
  ],
  "complexity": {{
    "time": "Big-O notation",
    "space": "Big-O notation",
    "readability": 8,
    "nesting_depth": 2
  }},
  "improvements": [
    "Tip 1..."
  ],
  "bugs": [
    {{
      "severity": "High | Medium | Low",
      "description": "bug description",
      "fix": "fix code"
    }}
  ],
  "quiz": [
    {{
      "question": "comprehension question",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "answer": "B) ...",
      "explanation": "logic description"
    }}
  ],
  "learning_tips": [
    "recommendation 1"
  ]
}}
"""


def _get_default_analysis_result(language: str, error_msg: str = "") -> dict[str, Any]:
    """Return a non-crashing safe dictionary structure loaded with standard default fallbacks."""
    return {
        "summary": f"Could not perform automated analysis. {error_msg}".strip(),
        "difficulty": "Beginner",
        "line_by_line": [("Line 1", "# Parsing failed", "Please review the source or try again.")],
        "complexity": {
            "time": "N/A",
            "space": "N/A",
            "readability": 5,
            "nesting_depth": 0,
            "difficulty": "Beginner"
        },
        "improvements": ["Could not extract code improvement suggestions."],
        "bugs": [],
        "quiz": [],
        "learning_tips": ["Review basic programming paradigms and try re-submitting the code."]
    }


def generate_complete_analysis(code: str, language: str) -> dict[str, Any]:
    """
    Request a single comprehensive code analysis from the Gemini API.

    Ensures robust stripping of Markdown fences, handles invalid JSON parsed outputs,
    and returns a structured Python dictionary suitable for direct state loading.

    Args:
        code: Source code string.
        language: User selected / detected programming language.

    Returns:
        Structured Python dictionary with all analysis categories. Always returns a dict.
    """
    try:
        model = _get_generative_model()
        prompt = _get_complete_analysis_prompt(code, language)

        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        )
        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        # Clean markdown code fences if Gemini ignores prompt constraints
        text = response.text.strip()
        if text.startswith("```"):
            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)
        if not isinstance(data, dict):
            logger.warning("Gemini did not return a JSON dictionary. Defaulting.")
            return _get_default_analysis_result(language, "API response was not a dictionary.")

        # Map response fields to match st.session_state.analysis_result schema precisely
        # 1. Summary
        summary = data.get("summary", "No summary provided.")
        difficulty = data.get("difficulty", "Beginner")

        # 2. Line by line tuples
        line_by_line_raw = data.get("line_by_line", [])
        line_by_line_mapped = []
        for idx, item in enumerate(line_by_line_raw, start=1):
            label = item.get("label", f"Line {item.get('line_number', idx)}")
            line_by_line_mapped.append((
                label,
                item.get("code", ""),
                item.get("explanation", "No explanation generated.")
            ))

        # 3. Complexity
        comp_raw = data.get("complexity", {})
        complexity_mapped = {
            "time": comp_raw.get("time", "N/A"),
            "space": comp_raw.get("space", "N/A"),
            "readability": comp_raw.get("readability", 5),
            "nesting_depth": comp_raw.get("nesting_depth", 0),
            "difficulty": difficulty
        }

        # 4. Improvements
        improvements = data.get("improvements", [])

        # 5. Bugs
        bugs_raw = data.get("bugs", [])
        bugs_mapped = []
        for bug in bugs_raw:
            bugs_mapped.append({
                "severity": bug.get("severity", "Medium"),
                "description": bug.get("description", "Potential issue identified."),
                "fix": bug.get("fix", "")
            })

        # 6. Quiz
        quiz_raw = data.get("quiz", [])
        quiz_mapped = []
        for q in quiz_raw:
            quiz_mapped.append({
                "question": q.get("question", "No question text"),
                "options": q.get("options", []),
                "answer": q.get("answer", ""),
                "explanation": q.get("explanation", "No explanation provided.")
            })

        # 7. Learning tips
        learning_tips = data.get("learning_tips", [])

        return {
            "language": language,
            "summary": summary,
            "line_by_line": line_by_line_mapped,
            "complexity": complexity_mapped,
            "improvements": improvements,
            "bugs": bugs_mapped,
            "quiz": quiz_mapped,
            "learning_tips": learning_tips
        }

    except Exception as err:
        err_msg = str(err)
        logger.error(f"Gemini processing error occurred: {err_msg}")
        try:
            raw_preview = response.text[:300] if 'response' in locals() and response.text else "N/A"
            logger.error(f"Raw response preview (first 300 chars): {raw_preview}")
        except Exception:
            pass
        return _get_default_analysis_result(language, f"Processing error: {err_msg}")
