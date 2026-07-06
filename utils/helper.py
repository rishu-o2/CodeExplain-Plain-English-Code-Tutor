# =============================================================================
# utils/helper.py — General-Purpose Helper Utilities
# =============================================================================
# Provides shared, reusable functions used across the application:
#
#   File I/O
#   --------
#   - load_sample_code()     : Safely reads a sample code file from disk.
#   - load_css()             : Injects a CSS file into the Streamlit page.
#
#   Streamlit UI Components
#   -----------------------
#   - render_placeholder()   : Renders a styled info banner for unimplemented tabs.
#   - render_section_header(): Renders a consistent section heading with divider.
#   - render_empty_card()    : Renders a bordered placeholder card with body text.
#   - render_language_badge(): Renders the detected-language pill badge.
#
# All functions here are pure helpers — they contain no business logic.
# Future AI modules (gemini_client, quiz_generator, etc.) should NOT be
# imported from this file; keep this module dependency-free.
# =============================================================================

from __future__ import annotations

import os
import streamlit as st


# ---------------------------------------------------------------------------
# FILE I/O HELPERS
# ---------------------------------------------------------------------------

# Maps each language name to its corresponding sample file in sample_codes/.
SAMPLE_FILE_MAP: dict[str, str] = {
    "Python":     os.path.join("sample_codes", "python_example.py"),
    "Java":       os.path.join("sample_codes", "java_example.java"),
    "C++":        os.path.join("sample_codes", "cpp_example.cpp"),
    "JavaScript": os.path.join("sample_codes", "javascript_example.js"),
}

# Default fallback shown when "Auto Detect" is selected or file load fails.
_FALLBACK_CODE = """\
def fibonacci(n):
    \"\"\"Return the nth Fibonacci number using recursion.\"\"\"
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
"""


def load_sample_code(language: str) -> str:
    """
    Load and return the sample code for the given language.

    Reads the appropriate file from the ``sample_codes/`` directory.
    If the file is missing or unreadable, returns a built-in fallback
    snippet so the application never crashes on a missing asset.

    Args:
        language: One of "Python", "Java", "C++", "JavaScript",
                  or "Auto Detect".

    Returns:
        The file contents as a plain string.
    """
    filepath = SAMPLE_FILE_MAP.get(language)

    if filepath is None:
        # "Auto Detect" selected — use the Python sample as the default.
        filepath = SAMPLE_FILE_MAP["Python"]

    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        st.warning(
            f"⚠️ Sample file not found: `{filepath}`. "
            "Showing built-in fallback code instead."
        )
        return _FALLBACK_CODE
    except OSError as exc:
        st.warning(f"⚠️ Could not read sample file: {exc}. Using fallback.")
        return _FALLBACK_CODE


def load_css(filepath: str) -> None:
    """
    Read a CSS file and inject it into the Streamlit page via a
    ``<style>`` block.  Fails silently if the file does not exist,
    so missing CSS never prevents the app from starting.

    Args:
        filepath: Relative or absolute path to the ``.css`` file.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            css = fh.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass  # CSS is optional; skip silently.


# ---------------------------------------------------------------------------
# REUSABLE STREAMLIT UI COMPONENTS
# ---------------------------------------------------------------------------

def render_section_header(title: str, divider: bool = False) -> None:
    """
    Render a consistent ``####`` section heading inside a tab or container.

    Args:
        title:   The heading text (may include leading emoji).
        divider: If True, draw a horizontal rule below the heading.
    """
    st.markdown(f"#### {title}")
    if divider:
        st.markdown("---")


def render_placeholder(message: str) -> None:
    """
    Render a styled informational banner that signals a tab is not yet
    connected to the AI backend.

    Args:
        message: The descriptive placeholder text shown to the user.
    """
    st.info(f"🔄 **Placeholder** — {message}")


def render_empty_card(body: str, icon: str = "📌") -> None:
    """
    Render a bordered card containing placeholder body text.  Used to
    preview the future output format of each analysis tab.

    Args:
        body: The markdown string displayed inside the card.
        icon: An optional leading emoji prepended to ``body``.
    """
    with st.container(border=True):
        st.markdown(f"{icon} {body}")


def render_language_badge(language: str) -> None:
    """
    Render a pill-shaped badge that shows the detected (or selected)
    programming language above the results tabs.

    Args:
        language: The language string, e.g. ``"Python"`` or ``"Auto Detect"``.
    """
    display = language if language != "Auto Detect" else "Python (detected)"
    st.markdown(
        f"<span style='"
        f"background:#1e3a5f;"
        f"color:#7eb8f7;"
        f"padding:4px 12px;"
        f"border-radius:20px;"
        f"font-size:0.85rem;"
        f"'>"
        f"🔤 Language: <strong>{display}</strong>"
        f"</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)
