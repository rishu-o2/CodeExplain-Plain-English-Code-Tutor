
# utils/language_detector.py — Programming Language Auto-Detection
# Detects the programming language of a given code snippet using:
#   - Score-based heuristic rules (keywords, common syntax elements)
#
# Supported languages: Python, JavaScript, Java, C++.

import re

def detect_language(code: str) -> str:
    """
    Perform rule-based heuristics to auto-detect the programming language.

    Scores the code snippet against syntax patterns characteristic of
    Python, Java, C++, and JavaScript. The language with the highest score
    is returned.

    Args:
        code: The raw code snippet.

    Returns:
        One of: "Python", "Java", "C++", "JavaScript". Defaults to "Python".
    """
    if not code or not code.strip():
        return "Python"

    scores = {
        "Python": 0,
        "Java": 0,
        "C++": 0,
        "JavaScript": 0
    }

    lines = code.splitlines()

    # Regex patterns for various syntax features
    python_patterns = [
        r"^\s*def\s+\w+\s*\(",
        r"^\s*elif\s+",
        r"^\s*import\s+\w+",
        r"^\s*from\s+\w+\s+import",
        r"^\s*#",
        r"print\s*\(",
        r"__name__\s*==\s*['\"]__main__['\"]",
        r"^\s*class\s+\w+(\s*\(.*\))?\s*:",
        r"\s+not\s+in\s+",
        r"\bNone\b"
    ]

    java_patterns = [
        r"^\s*public\s+class\s+\w+",
        r"System\.out\.print",
        r"public\s+static\s+void\s+main",
        r"^\s*import\s+java\.",
        r"\bpackage\s+\w+",
        r"\bextends\s+\w+",
        r"\bimplements\s+\w+",
        r"@Override",
        r"\bString\[\]\s+args\b",
        r"\bpublic\s+(static\s+)?(final\s+)?(void|int|double|float|boolean|char|String)\s+\w+\s*\(",
        r"\bprivate\s+(static\s+)?(final\s+)?(void|int|double|float|boolean|char|String)\s+\w+\s*\("
    ]

    cpp_patterns = [
        r"#include\s*<.*>",
        r"#include\s*\".*\"",
        r"\bstd::",
        r"\bcout\s*<<",
        r"\bcin\s*>>",
        r"using\s+namespace\s+std\s*;",
        r"\bint\s+main\s*\(\s*\)",
        r"\bnullptr\b",
        r"\bvector\s*<.*>",
        r"\bstd::string\b",
        r"\bstd::vector\b"
    ]

    js_patterns = [
        r"\bconst\s+\w+\s*=",
        r"\blet\s+\w+\s*=",
        r"\bvar\s+\w+\s*=",
        r"console\.log",
        r"\bfunction\s+\w+\s*\(",
        r"\bfunction\s*\(",
        r"\w+\s*=>",
        r"document\.get",
        r"\brequire\s*\(",
        r"export\s+default\b",
        r"===",
        r"!\s*=="
    ]

    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue

        # Check Python patterns
        for pattern in python_patterns:
            if re.search(pattern, line):
                scores["Python"] += 2

        # Check Java patterns
        for pattern in java_patterns:
            if re.search(pattern, line):
                scores["Java"] += 2

        # Check C++ patterns
        for pattern in cpp_patterns:
            if re.search(pattern, line):
                scores["C++"] += 2

        # Check JavaScript patterns
        for pattern in js_patterns:
            if re.search(pattern, line):
                scores["JavaScript"] += 2

        # General comments heuristics
        if cleaned_line.startswith("#"):
            scores["Python"] += 1
        elif cleaned_line.startswith("//"):
            scores["Java"] += 1
            scores["C++"] += 1
            scores["JavaScript"] += 1

    # Find the language with the maximum score
    detected_lang = max(scores, key=scores.get)
    
    # If no positive matches are found, default to Python
    if scores[detected_lang] == 0:
        return "Python"

    return detected_lang
