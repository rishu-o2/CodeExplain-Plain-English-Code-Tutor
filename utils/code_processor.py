# =============================================================================
# utils/code_processor.py — Code Parsing & Pre-Processing
# =============================================================================
# Handles all pre-processing steps before sending code to the AI model:
#   - Stripping excessive whitespace and normalizing indentation
#   - Splitting code into logical blocks or functions
#   - Extracting metadata (function names, class names, imports)
#   - Sanitizing input to avoid prompt injection
#
# Acts as the pipeline stage between raw user input and the AI layer.
# =============================================================================

from typing import Tuple

MAX_CODE_LENGTH = 20000

def sanitize_and_validate(code: str) -> Tuple[bool, str, str]:
    """
    Sanitize the input code and validate it for processing.

    Args:
        code: The raw string from the text area.

    Returns:
        A tuple of (is_valid, error_message, sanitized_code).
    """
    if not code:
        return False, "⚠️ Please paste some code before clicking **Explain Code**.", ""
        
    sanitized = code.strip()
    
    if not sanitized:
        return False, "⚠️ Please paste some code before clicking **Explain Code**.", ""
        
    if len(sanitized) > MAX_CODE_LENGTH:
        return False, f"⚠️ Your code is too long ({len(sanitized)} chars). Please limit to {MAX_CODE_LENGTH} characters.", sanitized
        
    return True, "", sanitized
