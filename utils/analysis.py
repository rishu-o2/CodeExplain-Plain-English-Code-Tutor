# =============================================================================
# utils/analysis.py — Code Analysis & Metrics
# =============================================================================
# Provides deeper static analysis of code snippets, including:
#   - Complexity scoring (cyclomatic complexity, nesting depth)
#   - Identifying key programming concepts (loops, recursion, OOP, etc.)
#   - Flagging potential issues or anti-patterns for educational feedback
#   - Summarizing code structure for report generation
# =============================================================================

from typing import Any

def calculate_static_metrics(code: str) -> dict[str, int]:
    """
    Calculate static metrics from the given code snippet.

    Args:
        code: The raw code string.

    Returns:
        A dictionary containing 'lines_count' and 'def_count'.
    """
    if not code:
        return {"lines_count": 0, "def_count": 0}
        
    raw_lines = code.splitlines()
    lines_count = len([l for l in raw_lines if l.strip()])
    
    keywords = ["def ", "function ", "class ", "void ", "fn "]
    def_count = sum(1 for line in raw_lines if any(kw in line for kw in keywords))
    
    return {
        "lines_count": lines_count,
        "def_count": def_count
    }
