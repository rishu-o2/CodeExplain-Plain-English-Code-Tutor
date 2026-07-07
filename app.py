# =============================================================================
# app.py — CodeExplain v1.0
# =============================================================================
# Streamlit entry point. Responsibilities:
#   - Page configuration and CSS injection
#   - Sidebar, header, input section, and output tabs
#   - Session-state initialisation
#   - Orchestrating the single Gemini analysis request
#
# Run with:  streamlit run app.py
# =============================================================================

from __future__ import annotations

import copy
import json
import logging
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.helper import (
    load_css,
    render_empty_card,
    render_error_card,
    render_history_panel,
    render_section_header,
    render_session_analytics,
)
import utils.analysis as analysis
import utils.code_processor as code_processor
import utils.gemini_client as gemini_client
import utils.language_detector as language_detector
import utils.report_generator as report_generator

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("app")


# =============================================================================
# PAGE CONFIGURATION
# Must be the very first Streamlit call in the script.
# =============================================================================
st.set_page_config(
    page_title="CodeExplain: Plain-English Code Tutor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS — all visual styles live in assets/styles.css.
load_css("assets/styles.css")


APP_NAME:     str = "CodeExplain"
APP_SUBTITLE: str = "Plain-English Code Tutor"
APP_VERSION:  str = "1.0.0"

DEFAULT_LANGUAGE: str = "Auto Detect"

SUPPORTED_LANGUAGES: list[str] = [
    DEFAULT_LANGUAGE,
    "Python",
    "Java",
    "C++",
    "JavaScript",
]

LANGUAGE_ICONS: dict[str, str] = {
    "Python":     "🐍",
    "Java":       "☕",
    "C++":        "⚙️",
    "JavaScript": "🌐",
}

# Tab labels — clean names, no emoji clutter.
TAB_SUMMARY:     str = "Summary"
TAB_LINEBY:      str = "Line-by-Line"
TAB_COMPLEXITY:  str = "Complexity"
TAB_IMPROVEMENT: str = "Improvements"
TAB_BUGS:        str = "Bugs"
TAB_QUIZ:        str = "Quiz"
TAB_LEARNING:    str = "Learning Tips"

ALL_TABS: list[str] = [
    TAB_SUMMARY, TAB_LINEBY, TAB_COMPLEXITY,
    TAB_IMPROVEMENT, TAB_BUGS, TAB_QUIZ, TAB_LEARNING,
]


#: Schema for the single analysis result object stored in session state.
_ANALYSIS_RESULT_SCHEMA: dict = {
    "language":     None,
    "summary":      None,
    "line_by_line": [],
    "complexity": {
        "time":          None,
        "space":         None,
        "readability":   None,
        "difficulty":    None,
        "nesting_depth": None,
    },
    "improvements":  [],
    "bugs":          [],
    "quiz":          [],
    "learning_tips": [],
    "report_path":   None,
}


def _init_session_state() -> None:
    """Initialise all session-state keys on first run."""
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)

    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0

    if "analysis_history" not in st.session_state:
        st.session_state.analysis_history = []

    if "session_stats" not in st.session_state:
        st.session_state.session_stats = {
            "analyses":    0,
            "files_uploaded": 0,
            "start_time": datetime.now(),
            "total_length": 0,
            "lang_counts": {},
        }

    if "cached_metrics_hash" not in st.session_state:
        st.session_state.cached_metrics_hash = None
        st.session_state.cached_metrics = {}

    if "code_input" not in st.session_state:
        st.session_state.code_input = ""


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> None:
    """
    Sidebar order (Task 4):
      1. Logo + project name
      2. Supported Languages
      3. Features
      4. Session Analytics (collapsed)
      5. Recent History (collapsed)
      6. About
    """
    with st.sidebar:

        # 1. Logo & name
        try:
            st.image("assets/logo.png", use_container_width=True)
        except Exception:
            st.markdown("## 🤖")
        st.markdown("## 🤖 CodeExplain")
        st.caption("Plain-English Code Tutor")
        st.divider()

        # 2. Supported Languages — badge row
        st.markdown("**Supported Languages**")
        badges = " &nbsp; ".join(
            f"<span class='lang-badge'>{icon} {lang}</span>"
            for lang, icon in LANGUAGE_ICONS.items()
        )
        st.markdown(f"<div class='lang-badges'>{badges}</div>", unsafe_allow_html=True)
        st.divider()

        # 3. Features list
        st.markdown("**Features**")
        for feat in [
            "Plain-English Summary",
            "Line-by-Line Breakdown",
            "Complexity Analysis",
            "Improvement Suggestions",
            "Bug Detection",
            "Interactive Quiz",
            "Learning Tips",
            "Downloadable Reports",
        ]:
            st.caption(f"\u2713 {feat}")
        st.divider()

        # 4. Session Analytics
        with st.expander("Session Analytics", expanded=False):
            if st.session_state.session_stats.get("analyses", 0) > 0:
                render_session_analytics(st.session_state.session_stats)
            else:
                st.caption("Available after your first analysis.")

        # 5. Recent History
        with st.expander("Recent History", expanded=False):
            if st.session_state.get("analysis_history"):
                render_history_panel(st.session_state.analysis_history, LANGUAGE_ICONS)
            else:
                st.caption("No history yet.")

        st.divider()

        # 6. About
        st.caption(
            "AI-powered code explanation for students and developers.\n"
            "Powered by Google Gemini."
        )
        st.markdown(
            f"<small style='color:var(--text-muted)'>🔖 v{APP_VERSION} · Built with Streamlit</small>",
            unsafe_allow_html=True,
        )



# =============================================================================
# HERO HEADER
# =============================================================================

def render_header() -> None:
    """
    Render the centred page title and subtitle.
    T3: single prominent title only, no duplicate branding.
    """
    st.markdown(
        "<h1 style='text-align:center;'>🤖 CodeExplain</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='hero-subtitle'>Understand any code in plain English — "
        "powered by Google Gemini.</p>",
        unsafe_allow_html=True,
    )


# =============================================================================
# CODE INPUT SECTION
# =============================================================================

def render_input_section() -> tuple[str, str, bool]:
    """
    Render the upload widget, code editor, language selector, and action buttons.

    Returns:
        code        – Raw code string from the text area.
        language    – Selected language.
        explain_btn – True when the Analyze Code button is clicked.
    """
    uploader_key = st.session_state.get("uploader_key", 0)
    uploaded_file = st.file_uploader(
        "Upload File",
        type=["py", "js", "java", "cpp", "c", "h", "txt"],
        key=f"uploader_{uploader_key}",
        help="Supported: Python • Java • JavaScript • C++",
    )

    if uploaded_file is not None:
        if st.session_state.get("uploaded_file_name") != uploaded_file.name:
            try:
                file_contents = uploaded_file.getvalue().decode("utf-8")
                st.session_state["code_input"] = file_contents
                st.session_state["uploaded_file_name"] = uploaded_file.name
                if "session_stats" in st.session_state:
                    st.session_state.session_stats["files_uploaded"] += 1
                ext = uploaded_file.name.split(".")[-1].lower()
                ext_map = {"py": "Python", "java": "Java", "cpp": "C++", "js": "JavaScript"}
                st.session_state["language_select"] = ext_map.get(ext, DEFAULT_LANGUAGE)
                st.rerun()
            except Exception as exc:
                st.error(f"Error reading file: {exc}")

    selected_language: str = st.session_state.get("language_select", DEFAULT_LANGUAGE)

    # Editor stays empty until the user pastes or uploads code.
    code_value = st.session_state.get("code_input") or ""
    code: str = st.text_area(
        label="Code Input",
        value=code_value,
        height=220,
        placeholder="Paste your Python, Java, C++, or JavaScript code here…",
        label_visibility="collapsed",
        key="code_input",
    )

    # Source code preview (only when there is code to show)
    if code.strip():
        filename = st.session_state.get("uploaded_file_name")
        preview_lang = selected_language.lower() if selected_language != "Auto Detect" else "python"
        with st.expander("Source Code Preview", expanded=False):
            if filename:
                st.caption(f"File: {filename}")
            st.code(code, language=preview_lang, line_numbers=True)

    col_lang, col_btn, col_clear = st.columns([2, 1.5, 1])

    with col_lang:
        language: str = st.selectbox(
            label="Language",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(DEFAULT_LANGUAGE),
            key="language_select",
            help="Select the language or choose Auto Detect.",
        )

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        explain_btn: bool = st.button(
            "Explain Code",
            type="primary",
            width="stretch",
            key="explain_btn",
            help="Analyse your code using Google Gemini AI",
        )

    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear", type="secondary", width="stretch", key="clear_btn"):
            st.session_state["code_input"] = ""
            st.session_state["has_analyzed"] = False
            st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)
            st.session_state["uploaded_file_name"] = None
            st.session_state["uploader_key"] = st.session_state.get("uploader_key", 0) + 1
            st.rerun()

    return code, language, explain_btn


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_input(code: str) -> tuple[bool, str]:
    """
    Validate user-supplied code before attempting any processing.
    """
    is_valid, error_msg, sanitized = code_processor.sanitize_and_validate(code)
    if not is_valid:
        st.warning(error_msg)
    logger.info("Validation completed")
    return is_valid, sanitized


# =============================================================================
# INDIVIDUAL TAB RENDERERS
# =============================================================================

def render_summary_tab(code: str) -> None:
    """Tab 1 — Plain-English Summary."""
    result = st.session_state.analysis_result
    render_section_header("Plain-English Summary")

    summary_text = result.get("summary")
    if not summary_text:
        st.info("No summary was returned for this analysis.")
        return

    st.markdown(summary_text)
    st.markdown("---")

    metrics = analysis.calculate_static_metrics(code)
    lines_count = metrics.get("lines_count", 0)
    def_count = metrics.get("def_count", 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Lines of Code", value=str(lines_count))
    with col2:
        st.metric(label="Functions / Classes", value=str(def_count))


def render_linebyline_tab() -> None:
    """Tab 2 — Line-by-Line Explanation."""
    result = st.session_state.analysis_result
    render_section_header("Line-by-Line Explanation")

    rows = result.get("line_by_line", [])
    if not rows:
        st.info("No line-by-line breakdown was returned for this analysis.")
        return

    lang = str(result.get("language", "python")).lower()
    lang_highlight = "python"
    if "javascript" in lang:
        lang_highlight = "javascript"
    elif "c++" in lang or "cpp" in lang:
        lang_highlight = "cpp"
    elif "java" in lang:
        lang_highlight = "java"

    for label, code_line, explanation in rows:
        preview = code_line.strip()
        if len(preview) > 40:
            preview = preview[:40] + "..."
        with st.expander(f"**{label}:** `{preview}`"):
            col_code, col_exp = st.columns([1, 2])
            with col_code:
                st.code(code_line, language=lang_highlight)
            with col_exp:
                st.markdown(f"**Explanation:**\n\n{explanation}")


def render_complexity_tab() -> None:
    """Tab 3 — Complexity Analysis."""
    result = st.session_state.analysis_result
    render_section_header("Complexity Analysis")

    complexity = result.get("complexity", {})
    if not complexity or complexity.get("time") is None:
        st.info("No complexity analysis was returned for this analysis.")
        return

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**Algorithmic Complexity**")
        st.metric(label="Time Complexity", value=complexity.get("time", "N/A"))
        st.metric(label="Space Complexity", value=complexity.get("space", "N/A"))
    with col_right:
        st.markdown("**Code Metrics**")
        st.metric(label="Nesting Depth", value=str(complexity.get("nesting_depth", "N/A")))
        st.metric(label="Readability", value=f"{complexity.get('readability', 'N/A')}/10")
        st.metric(label="Difficulty", value=complexity.get("difficulty", "N/A"))


def render_improvement_tab() -> None:
    """Tab 4 — Suggested Improvements."""
    result = st.session_state.analysis_result
    render_section_header("Suggested Improvements")

    improvements = result.get("improvements", [])
    if not improvements:
        st.info("No improvement suggestions were returned for this analysis.")
        return

    for imp in improvements:
        render_empty_card(imp, icon="✓")


def render_bug_tab() -> None:
    """Tab 5 — Potential Bugs & Issues."""
    result = st.session_state.analysis_result
    render_section_header("Bugs & Issues")

    bugs = result.get("bugs", [])
    if not bugs:
        st.success("No bugs, anti-patterns, or logic errors were identified.")
        return

    lang = str(result.get("language", "python")).lower()
    lang_highlight = "python"
    if "javascript" in lang:
        lang_highlight = "javascript"
    elif "c++" in lang or "cpp" in lang:
        lang_highlight = "cpp"
    elif "java" in lang:
        lang_highlight = "java"

    for idx, bug in enumerate(bugs, start=1):
        severity = str(bug.get("severity", "Medium")).lower()
        desc = bug.get("description", "")
        fix = bug.get("fix", "")

        box_title = f"Issue {idx} ({severity.capitalize()} Severity)"
        with st.expander(box_title):
            if "high" in severity:
                st.error(f"**{box_title}**\n\n{desc}")
            elif "medium" in severity:
                st.warning(f"**{box_title}**\n\n{desc}")
            else:
                st.info(f"**{box_title}**\n\n{desc}")

            if fix.strip():
                st.markdown("**Suggested Fix:**")
                st.code(fix, language=lang_highlight)


def render_quiz_tab() -> None:
    """Tab 6 — Comprehension Quiz."""
    result = st.session_state.analysis_result
    render_section_header("Comprehension Quiz")

    quiz_questions = result.get("quiz", [])
    if not quiz_questions:
        st.info("No quiz questions were returned for this analysis.")
        return

    correct_answers = 0
    total_questions = len(quiz_questions)
    answered_questions = 0

    for idx, q in enumerate(quiz_questions):
        st.markdown(f"##### Q{idx + 1}. {q.get('question')}")

        options = q.get("options", [])
        correct_answer = q.get("answer", "")
        explanation = q.get("explanation", "")

        user_choice = st.radio(
            label=f"q_{idx}_label",
            options=options,
            index=None,
            key=f"quiz_q_{idx}",
            label_visibility="collapsed",
        )

        if user_choice:
            answered_questions += 1
            if user_choice == correct_answer:
                correct_answers += 1
                st.success(f"✅ **Correct!** {explanation}")
            else:
                st.error(f"❌ **Incorrect.** The correct answer is: **{correct_answer}**\n\n{explanation}")
        st.markdown("---")

    st.session_state.quiz_score = correct_answers

    col_score, col_submit = st.columns([3, 1])
    with col_score:
        st.markdown(f"**Score: {correct_answers} / {total_questions}**")
    with col_submit:
        all_done = answered_questions == total_questions
        if st.button("Submit Quiz", disabled=not all_done, width="stretch", key="submit_quiz"):
            if correct_answers == total_questions:
                st.balloons()
                st.success("Perfect Score! Excellent understanding of the code.")
            else:
                st.info("Quiz submitted. Review incorrect answers to learn more.")


def render_learning_tab() -> None:
    """Tab 7 — Learning Tips."""
    result = st.session_state.analysis_result
    render_section_header("Learning Tips")

    tips = result.get("learning_tips", [])
    if not tips:
        st.info("No learning tips were returned for this analysis.")
        return

    for tip in tips:
        icon = "→"
        render_empty_card(tip, icon=icon)


# =============================================================================
# PRIVATE UI HELPERS
# =============================================================================

def _show_progress(
    slot,
    done: list[str],
    active: str,
    pending: list[str],
    pct: float,
) -> None:
    """
    Update a Streamlit ``st.empty()`` slot in-place with a styled progress card.
    """
    lines_html = "".join(f"<div class='prog-step done'>✓ {s}</div>" for s in done)
    if active:
        lines_html += f"<div class='prog-step active'>⏳ {active}</div>"
    lines_html += "".join(f"<div class='prog-step pending'>· {s}</div>" for s in pending)

    with slot.container():
        st.markdown(f'<div class="progress-card">{lines_html}</div>', unsafe_allow_html=True)
        st.progress(pct)


def _render_stats_dashboard(code: str, result: dict) -> None:
    """
    Render the statistics dashboard.
    """
    code_hash = hash(code)
    if st.session_state.get("cached_metrics_hash") != code_hash:
        st.session_state.cached_metrics      = analysis.calculate_static_metrics(code)
        st.session_state.cached_metrics_hash = code_hash

    metrics    = st.session_state.cached_metrics
    struct     = metrics.get("structure", {})
    quality    = metrics.get("quality", {})
    compl      = metrics.get("complexity", {})
    lang       = result.get("language", "—") or "—"
    difficulty = (result.get("complexity") or {}).get("difficulty") or "—"

    metrics_data = [
        ("Lines of Code",     str(struct.get("Lines of code", 0))),
        ("Functions",         str(struct.get("Function count", 0))),
        ("Classes",           str(struct.get("Class count", 0))),
        ("Est. Complexity",   compl.get("Estimated Time Complexity", "—")),
        ("Difficulty",        difficulty),
        ("Language",          lang),
        ("Maintainability",   quality.get("Maintainability score", "—")),
        ("Readability",       quality.get("Readability score", "—")),
    ]

    st.markdown("#### Code Statistics")
    cols = st.columns(4)
    for i, (label, value) in enumerate(metrics_data):
        with cols[i % 4]:
            st.metric(label=label, value=value)
    st.markdown("---")


# =============================================================================
# OUTPUT TAB ORCHESTRATOR
# =============================================================================

def render_output_tabs(code: str, language: str) -> None:
    """Render the analysis results once the user has completed an analysis."""
    st.divider()

    result = st.session_state.analysis_result

    st.markdown("### Analysis Results")
    _render_stats_dashboard(code, result)
    logger.info("UI rendering completed")

    with st.expander("📥 Download Results", expanded=False):
        dl1, dl2, dl3 = st.columns(3)
        with dl1:
            md_content = report_generator.generate_markdown_report(result, code)
            st.download_button("Markdown", data=md_content, file_name="code_report.md",
                               mime="text/markdown", use_container_width=True)
        with dl2:
            html_content = report_generator.generate_html_report(result, code)
            st.download_button("HTML", data=html_content, file_name="code_report.html",
                               mime="text/html", use_container_width=True)
        with dl3:
            json_content = json.dumps(result, indent=2)
            st.download_button("JSON", data=json_content, file_name="code_report.json",
                               mime="application/json", use_container_width=True)

    (
        tab_summary,
        tab_lineby,
        tab_complexity,
        tab_improvements,
        tab_bugs,
        tab_quiz,
        tab_learning,
    ) = st.tabs(ALL_TABS)

    with tab_summary:
        render_summary_tab(code)
    with tab_lineby:
        render_linebyline_tab()
    with tab_complexity:
        render_complexity_tab()
    with tab_improvements:
        render_improvement_tab()
    with tab_bugs:
        render_bug_tab()
    with tab_quiz:
        render_quiz_tab()
    with tab_learning:
        render_learning_tab()


# =============================================================================
# PHASE 3 INTEGRATION POINT
# =============================================================================

def process_code(code: str, language: str) -> None:
    """
    Phase 3 integration point — orchestrates all AI analysis modules.

    Calls the single unified generate_complete_analysis() method from gemini_client
    and maps the returned values directly into st.session_state.analysis_result keys.
    On failure, classifies the error type into session state for Task 10 display.

    Args:
        code:     The raw code string submitted by the user.
        language: The language selected in the dropdown (or auto-detected).
    """
    logger.info("Analysis started")

    # Clear any previous error state
    st.session_state.pop("analysis_error_type", None)
    st.session_state.pop("analysis_error_detail", None)

    # 1. Reset analysis_result to baseline schema with the active language
    st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)
    st.session_state.analysis_result["language"] = language

    try:
        logger.info("Gemini request started")
        # Single request execution — do NOT rename this variable (would shadow the module)
        ai_result = gemini_client.generate_complete_analysis(code, language)
        logger.info("Gemini response received")

        # Map AI response fields into session state
        st.session_state.analysis_result["summary"]       = ai_result.get("summary", "")
        st.session_state.analysis_result["line_by_line"]  = ai_result.get("line_by_line", [])
        st.session_state.analysis_result["complexity"]    = ai_result.get("complexity", {})
        st.session_state.analysis_result["improvements"]  = ai_result.get("improvements", [])
        st.session_state.analysis_result["bugs"]          = ai_result.get("bugs", [])
        st.session_state.analysis_result["quiz"]          = ai_result.get("quiz", [])
        st.session_state.analysis_result["learning_tips"] = ai_result.get("learning_tips", [])

        # Reset running quiz score
        st.session_state.quiz_score = 0

        # Task 6 — update session analytics
        stats = st.session_state.session_stats
        stats["analyses"]   += 1
        stats["total_length"] += len(code)
        stats["lang_counts"][language] = stats["lang_counts"].get(language, 0) + 1

        # Task 7 — append enriched history item
        difficulty = (st.session_state.analysis_result.get("complexity") or {}).get("difficulty", "—") or "—"
        history_item = {
            "timestamp":   datetime.now().strftime("%H:%M:%S"),
            "language":    language,
            "code":        code,
            "code_length": len(code),       # shown in history panel
            "difficulty":  difficulty,       # shown in history panel
            "result":      copy.deepcopy(st.session_state.analysis_result),
        }
        st.session_state.analysis_history.append(history_item)
        logger.info("Session state updated")

    except Exception as e:
        logger.error(f"Failed to process unified code analysis: {e}")
        st.session_state.quiz_score = 0

        # Task 10 — classify error for rich error card display
        err_lower = str(e).lower()
        if "api_key" in err_lower or "api key" in err_lower or "invalid key" in err_lower:
            err_type = "no_api_key"
        elif "quota" in err_lower or "rate" in err_lower or "429" in err_lower:
            err_type = "gemini_unavailable"
        elif "network" in err_lower or "connection" in err_lower or "timeout" in err_lower:
            err_type = "network_error"
        elif "json" in err_lower or "parse" in err_lower or "decode" in err_lower:
            err_type = "invalid_response"
        else:
            err_type = "generic"
        st.session_state.analysis_error_type   = err_type
        st.session_state.analysis_error_detail = str(e)[:300]


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================


def main() -> None:
    """Top-level orchestrator."""
    _init_session_state()
    render_sidebar()
    render_header()

    code, language, explain_clicked = render_input_section()

    if explain_clicked:
        is_valid, code_sanitized = validate_input(code)
        if is_valid:
            prog_slot = st.empty()
            _show_progress(prog_slot, [], "Preparing source code…",
                           ["Detecting language", "Sending to Gemini", "Parsing response", "Building report"], 0.1)

            language_used = (
                language_detector.detect_language(code_sanitized)
                if language == DEFAULT_LANGUAGE else language
            )
            logger.info("Language detected: %s", language_used)
            st.session_state.analysis_result["language"] = language_used
            _show_progress(prog_slot, ["Prepared source code"],
                           f"Language: {language_used} — Sending to Gemini…",
                           ["Parsing response", "Building report"], 0.35)

            process_code(code_sanitized, language_used)

            if st.session_state.get("analysis_error_type"):
                prog_slot.empty()
                render_error_card(
                    st.session_state.analysis_error_type,
                    st.session_state.get("analysis_error_detail", ""),
                )
            else:
                _show_progress(prog_slot,
                               ["Prepared source code", f"Language: {language_used}",
                                "Gemini responded", "Parsed AI response"],
                               "Building analysis report…", [], 0.9)
                time.sleep(0.3)
                _show_progress(prog_slot,
                               ["Prepared source code", f"Language: {language_used}",
                                "Gemini responded", "Parsed AI response", "Analysis complete ✓"],
                               "", [], 1.0)
                time.sleep(0.35)
                prog_slot.empty()
                st.session_state.has_analyzed = True
                render_output_tabs(code_sanitized, language_used)

    elif st.session_state.get("has_analyzed", False):
        language_used = st.session_state.analysis_result.get("language", language)
        render_output_tabs(code, language_used)


if __name__ == "__main__":
    main()

