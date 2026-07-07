# =============================================================================
# utils/helper.py — Shared Helper Utilities
# =============================================================================
# Provides reusable UI and utility helpers used across the Streamlit app.
# =============================================================================

from __future__ import annotations

import copy
from datetime import datetime

import streamlit as st


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
# CORE REUSABLE UI COMPONENTS (original)
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


def render_empty_card(body: str, icon: str = "📌") -> None:
    """
    Render a bordered card for analysis content.

    Args:
        body: The markdown string displayed inside the card.
        icon: An optional leading emoji prepended to ``body``.
    """
    with st.container(border=True):
        st.markdown(f"{icon} {body}")


# ---------------------------------------------------------------------------
# TASK 10 — STRUCTURED ERROR CARDS
# ---------------------------------------------------------------------------

# Config: (title, problem, fix, severity) per error type.
_ERROR_CONFIGS: dict[str, tuple[str, str, str, str]] = {
    "no_api_key": (
        "🔑 API Key Not Found",
        "The `GEMINI_API_KEY` environment variable is missing or empty.",
        "Add `GEMINI_API_KEY=your_key_here` to your `.env` file and restart the app.",
        "error",
    ),
    "gemini_unavailable": (
        "☁️ Gemini Service Unavailable",
        "The Google Gemini API returned an error or is temporarily down.",
        "Wait a moment and click **Retry**. If the issue persists, "
        "check the Google Cloud status page.",
        "warning",
    ),
    "network_error": (
        "🌐 Network Connection Error",
        "Your device could not reach the Gemini API — the internet connection may be down.",
        "Check your network connection and click **Retry** below.",
        "warning",
    ),
    "invalid_response": (
        "🤖 Unexpected AI Response",
        "Gemini returned a response that could not be parsed correctly.",
        "Click **Retry**. If the snippet is very short or unusual, try adding more context.",
        "warning",
    ),
    "code_too_large": (
        "📏 Code Too Large",
        "The submitted code exceeds the maximum allowed character limit.",
        "Reduce the snippet to under 20,000 characters and try again.",
        "error",
    ),
    "generic": (
        "⚠️ Analysis Failed",
        "An unexpected error occurred during the analysis.",
        "Click **Retry** or refresh the page to start again.",
        "error",
    ),
}


def render_error_card(error_type: str, detail: str = "") -> None:
    """
    Render a structured error card showing problem, cause, fix, and retry.

    Args:
        error_type: One of the keys in ``_ERROR_CONFIGS``.
        detail:     Optional raw exception message for developer context.
    """
    title, problem, fix, severity = _ERROR_CONFIGS.get(
        error_type, _ERROR_CONFIGS["generic"]
    )
    detail_line = f"\n\n**Detail:** `{detail}`" if detail else ""
    content = (
        f"**{title}**\n\n"
        f"**Problem:** {problem}"
        f"{detail_line}\n\n"
        f"**How to fix:** {fix}"
    )
    if severity == "error":
        st.error(content)
    else:
        st.warning(content)
    if st.button("🔁 Retry Analysis", key="error_retry_btn"):
        st.rerun()


# ---------------------------------------------------------------------------
# TASK 6 — SESSION ANALYTICS SIDEBAR WIDGET
# ---------------------------------------------------------------------------

def render_session_analytics(stats: dict) -> None:
    """
    Render session statistics inside the sidebar.

    Reads from the ``session_stats`` dict stored in ``st.session_state``.
    Displays analyses count, files uploaded, average code length, most-used
    language, and elapsed session duration.

    Args:
        stats: The ``st.session_state.session_stats`` dict.
    """
    st.markdown("### 📈 Session Stats")

    analyses    = stats.get("analyses", 0)
    files_up    = stats.get("files_uploaded", 0)
    total_len   = stats.get("total_length", 0)
    avg_len     = (total_len // analyses) if analyses > 0 else 0
    start_time  = stats.get("start_time", datetime.now())
    elapsed_s   = int((datetime.now() - start_time).total_seconds())
    duration    = f"{elapsed_s // 60}m {elapsed_s % 60}s"
    lang_counts = stats.get("lang_counts", {})
    top_lang    = max(lang_counts, key=lang_counts.get) if lang_counts else "—"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Analyses", analyses)
        st.metric("Avg Length", f"{avg_len:,} ch")
        st.metric("Duration", duration)
    with col2:
        st.metric("Files Up", files_up)
        st.metric("Top Lang", top_lang)


# ---------------------------------------------------------------------------
# TASK 7 — IMPROVED HISTORY PANEL
# ---------------------------------------------------------------------------

def _render_single_history_item(actual_idx: int, hist: dict, language_icons: dict) -> None:
    """
    Render one history row with language icon, timestamp, code length,
    difficulty badge, a Load button, and a Delete button.

    Args:
        actual_idx:     The item's position in the original (non-reversed) list.
        hist:           The history dict for this item.
        language_icons: Mapping of language name → emoji (from app.py constants).
    """
    lang       = hist.get("language", "Code")
    icon       = language_icons.get(lang, "📄")
    ts         = hist.get("timestamp", "")
    code_len   = hist.get("code_length", len(hist.get("code", "")))
    difficulty = hist.get("difficulty", "")
    diff_label = f"&nbsp;·&nbsp;{difficulty}" if difficulty and difficulty != "—" else ""

    with st.container(border=True):
        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(
                f"<div class='hist-item'>"
                f"<strong>{icon} {lang}</strong>&nbsp;·&nbsp;<code>{ts}</code>{diff_label}"
                f"<br><small>{code_len:,} characters</small>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button("↩ Load", key=f"load_hist_{actual_idx}", use_container_width=True):
                st.session_state.analysis_result = copy.deepcopy(hist.get("result"))
                st.session_state.code_input      = hist.get("code", "")
                st.session_state.language_select = lang
                st.session_state.has_analyzed    = True
                st.rerun()
        with col_del:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️", key=f"del_hist_{actual_idx}", help="Remove this entry"):
                st.session_state.analysis_history.pop(actual_idx)
                st.rerun()


def render_history_panel(history: list, language_icons: dict) -> None:
    """
    Render the improved analysis history panel inside the sidebar.

    Shows items newest-first. Each item displays: language icon, timestamp,
    code length, and difficulty. Supports per-item delete and Clear All.

    Args:
        history:        ``st.session_state.analysis_history`` list.
        language_icons: Mapping of language name → emoji icon.
    """
    st.markdown("### 📜 History")

    if st.button("🗑️ Clear All", key="clear_history_btn", use_container_width=True):
        st.session_state.analysis_history = []
        st.rerun()

    total = len(history)
    for raw_idx, hist in enumerate(reversed(history)):
        actual_idx = total - 1 - raw_idx
        _render_single_history_item(actual_idx, hist, language_icons)
