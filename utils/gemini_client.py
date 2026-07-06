# =============================================================================
# utils/gemini_client.py — Google Gemini API Client Wrapper
# =============================================================================

from __future__ import annotations

import os
import json
import logging
import time
import re
from typing import Any
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# Setup module logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gemini_client")

MODEL_NAME = "gemini-2.5-flash"
MAX_RETRIES = 3
_cached_model: genai.GenerativeModel | None = None

def _get_generative_model() -> genai.GenerativeModel:
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable is not set.")
        raise ValueError("Gemini API Key is not set.")

    try:
        genai.configure(api_key=api_key)
        _cached_model = genai.GenerativeModel(MODEL_NAME)
        return _cached_model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {e}")
        raise RuntimeError(f"Failed to initialize Gemini API client: {e}") from e

def _get_complete_analysis_prompt(code: str, language: str) -> str:
    return f"""
Analyze the following {language} code snippet:

```
{code}
```

Instructions:
1. Return ONLY a single JSON object. No markdown, no explanations outside JSON.
2. Provide exactly these keys:
- "summary": (string) High-level overview.
- "difficulty": (string) "Beginner", "Intermediate", or "Advanced".
- "line_by_line": (list of objects) {{"label": "Line X", "code": "...", "explanation": "..."}}
- "complexity": (object) {{"time": "...", "space": "...", "readability": integer 1-10, "nesting_depth": integer}}
- "improvements": (list of strings) Max 3 optimizations.
- "bugs": (list of objects or empty array) {{"severity": "High|Medium|Low", "description": "...", "fix": "..."}}
- "quiz": (list of exactly 3 objects) {{"question": "...", "options": ["A)...", "B)...", "C)...", "D)..."], "answer": "...", "explanation": "..."}}
- "learning_tips": (list of strings) Recommendations.
"""

def _get_default_analysis_result(language: str, error_msg: str = "") -> dict[str, Any]:
    return {
        "language": language,
        "summary": f"Could not perform automated analysis. {error_msg}".strip(),
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

def _clean_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
    return text.strip()

def _extract_json(text: str) -> str:
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx+1]
    return text

def _parse_json(text: str) -> dict | None:
    cleaned = _extract_json(_clean_response(text))
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
    return None

def _validate_analysis(data: dict, language: str) -> dict[str, Any]:
    summary = str(data.get("summary", "No summary provided.")) if data.get("summary") else "No summary provided."
    difficulty = str(data.get("difficulty", "Beginner"))

    line_by_line_raw = data.get("line_by_line", [])
    if not isinstance(line_by_line_raw, list):
        line_by_line_raw = []
    line_by_line_mapped = []
    for idx, item in enumerate(line_by_line_raw, start=1):
        if isinstance(item, dict):
            label = str(item.get("label", f"Line {item.get('line_number', idx)}"))
            code = str(item.get("code", ""))
            explanation = str(item.get("explanation", "No explanation generated."))
            line_by_line_mapped.append((label, code, explanation))

    comp_raw = data.get("complexity", {})
    if not isinstance(comp_raw, dict):
        comp_raw = {}
    
    try:
        readability = int(comp_raw.get("readability", 5))
    except (ValueError, TypeError):
        readability = 5
        
    try:
        nesting_depth = int(comp_raw.get("nesting_depth", 0))
    except (ValueError, TypeError):
        nesting_depth = 0

    complexity_mapped = {
        "time": str(comp_raw.get("time", "N/A")),
        "space": str(comp_raw.get("space", "N/A")),
        "readability": readability,
        "nesting_depth": nesting_depth,
        "difficulty": difficulty
    }

    improvements_raw = data.get("improvements", [])
    improvements = [str(i) for i in improvements_raw] if isinstance(improvements_raw, list) else []

    bugs_raw = data.get("bugs", [])
    bugs_mapped = []
    if isinstance(bugs_raw, list):
        for bug in bugs_raw:
            if isinstance(bug, dict):
                bugs_mapped.append({
                    "severity": str(bug.get("severity", "Medium")),
                    "description": str(bug.get("description", "Potential issue identified.")),
                    "fix": str(bug.get("fix", ""))
                })

    quiz_raw = data.get("quiz", [])
    quiz_mapped = []
    if isinstance(quiz_raw, list):
        for q in quiz_raw:
            if isinstance(q, dict):
                options_raw = q.get("options", [])
                options = [str(o) for o in options_raw] if isinstance(options_raw, list) else []
                quiz_mapped.append({
                    "question": str(q.get("question", "No question text")),
                    "options": options,
                    "answer": str(q.get("answer", "")),
                    "explanation": str(q.get("explanation", "No explanation provided."))
                })

    learning_tips_raw = data.get("learning_tips", [])
    learning_tips = [str(t) for t in learning_tips_raw] if isinstance(learning_tips_raw, list) else []

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

def generate_complete_analysis(code: str, language: str) -> dict[str, Any]:
    logger.info(f"Analysis request started for language: {language}")
    
    try:
        model = _get_generative_model()
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        return _get_default_analysis_result(language, "Model initialization failed.")

    prompt = _get_complete_analysis_prompt(code, language)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "response_mime_type": "application/json"
                }
            )
            
            if not response.text:
                raise ValueError("Empty response text from Gemini.")
                
            parsed_data = _parse_json(response.text)
            if parsed_data is None:
                logger.error("Failed to parse JSON on attempt %d. Returning default.", attempt)
                return _get_default_analysis_result(language, "API response was not a valid dictionary.")
                
            logger.info("Analysis request completed successfully.")
            return _validate_analysis(parsed_data, language)
            
        except (GoogleAPIError, Exception) as e:
            logger.error(f"API request failed on attempt {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                sleep_time = 2 ** attempt
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("Max retries exceeded.")
                return _get_default_analysis_result(language, "Max retries exceeded during API request.")

    return _get_default_analysis_result(language, "Unknown error occurred.")
