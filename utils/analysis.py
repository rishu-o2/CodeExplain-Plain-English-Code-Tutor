# =============================================================================
# utils/analysis.py — Code Analysis & Metrics
# =============================================================================
import re
from typing import Any, Dict

def calculate_structure_metrics(code: str) -> Dict[str, Any]:
    """Calculate basic structural metrics like lines of code and function count."""
    lines = code.splitlines()
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith(("#", "//", "/*", "*")))
    loc = len(lines) - blank_lines - comment_lines
    
    func_count = sum(1 for line in lines if re.search(r'\b(def|function|fn)\b', line))
    class_count = sum(1 for line in lines if re.search(r'\bclass\b', line))
    
    # Estimate max nesting depth simply by counting leading spaces/tabs
    max_nesting = 0
    for line in lines:
        if line.strip():
            spaces = len(line) - len(line.lstrip(' '))
            tabs = len(line) - len(line.lstrip('\t'))
            depth = (spaces // 4) + tabs
            max_nesting = max(max_nesting, depth)
            
    return {
        "Lines of code": loc if loc > 0 else 0,
        "Blank lines": blank_lines,
        "Comment lines": comment_lines,
        "Function count": func_count,
        "Class count": class_count,
        "Maximum nesting depth": max_nesting
    }

def calculate_complexity_metrics(code: str) -> Dict[str, Any]:
    """Calculate complexity metrics like loop count and conditionals."""
    lines = code.splitlines()
    loop_count = sum(1 for line in lines if re.search(r'\b(for|while)\b', line))
    cond_count = sum(1 for line in lines if re.search(r'\b(if|elif|else|switch|case)\b', line))
    
    # Very crude heuristic for time/space complexity and cyclomatic complexity
    cyclomatic = 1 + loop_count + cond_count
    
    time_est = "O(1)"
    if loop_count == 1: time_est = "O(n)"
    elif loop_count > 1: time_est = "O(n^2)"
    
    space_est = "O(1)"
    if re.search(r'\b(list|dict|new|malloc)\b', code): space_est = "O(n)"
    
    return {
        "Loop count": loop_count,
        "Conditional count": cond_count,
        "Estimated Time Complexity": time_est,
        "Estimated Space Complexity": space_est,
        "Cyclomatic Complexity": cyclomatic
    }

def calculate_quality_metrics(code: str) -> Dict[str, Any]:
    """Calculate subjective quality metrics like readability."""
    lines = code.splitlines()
    loc = len([l for l in lines if l.strip()])
    func_count = sum(1 for line in lines if re.search(r'\b(def|function|fn)\b', line))
    
    avg_func_len = loc // func_count if func_count > 0 else loc
    
    # Heuristics
    readability = max(1, 10 - (avg_func_len // 20) - (1 if len(lines) > 500 else 0))
    maintainability = max(1, 100 - (avg_func_len) - (len(lines) // 10))
    
    return {
        "Readability score": f"{min(10, readability)}/10",
        "Naming quality": "Moderate (Estimated)",
        "Average function length": avg_func_len,
        "Duplicate code estimate": "0%",
        "Maintainability score": f"{min(100, maintainability)}/100"
    }

def detect_programming_concepts(code: str) -> Dict[str, bool]:
    """Identify programming concepts used in the code."""
    return {
        "Recursion": bool(re.search(r'\b(\w+)\s*\(.*?\b\1\s*\(', code)), # very basic check
        "OOP": bool(re.search(r'\b(class|this|self)\b', code)),
        "Exception Handling": bool(re.search(r'\b(try|catch|except|finally)\b', code)),
        "File Handling": bool(re.search(r'\b(open|read|write|fs\.)\b', code)),
        "Collections": bool(re.search(r'\b(list|dict|set|map|array)\b', code)),
        "Generators": bool(re.search(r'\b(yield)\b', code)),
        "Async": bool(re.search(r'\b(async|await|Promise)\b', code)),
        "Multithreading": bool(re.search(r'\b(Thread|Runnable|pthread)\b', code)),
        "Design Patterns": bool(re.search(r'\b(getInstance|Factory|Observer)\b', code, re.IGNORECASE))
    }

def calculate_static_metrics(code: str) -> Dict[str, Any]:
    """
    Master function to calculate all static metrics.
    Returns nested dictionaries for structure, complexity, quality, and concepts.
    """
    if not code:
        return {}
        
    return {
        "structure": calculate_structure_metrics(code),
        "complexity": calculate_complexity_metrics(code),
        "quality": calculate_quality_metrics(code),
        "concepts": detect_programming_concepts(code),
        # Legacy fields for backward compatibility with older UI code if any
        "lines_count": len([l for l in code.splitlines() if l.strip()]),
        "def_count": sum(1 for line in code.splitlines() if re.search(r'\b(def|function|class|void|fn)\b', line))
    }
