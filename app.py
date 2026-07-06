# =============================================================================
# app.py — Main Entry Point for CodeExplain: Plain-English Code Tutor
# =============================================================================
# Responsibilities (this file only):
#   - Streamlit page configuration & CSS injection
#   - Rendering sidebar, header, input section, and output tabs
#   - Session-state initialisation via a single structured object
#   - Orchestrating calls between UI sections
#
# What this file does NOT do:
#   - No hardcoded sample code  → loaded dynamically via utils.helper
#   - No inline CSS             → loaded from assets/styles.css via utils.helper
#   - No AI / Gemini logic      → reserved for utils/gemini_client.py
#   - No language detection     → reserved for utils/language_detector.py
#   - No complexity analysis    → reserved for utils/analysis.py
#   - No quiz generation        → reserved for utils/quiz_generator.py
#   - No report generation      → reserved for utils/report_generator.py
#
# Session-state contract (Phase 3 hook-up guide):
#   All AI output is stored in ONE object: st.session_state.analysis_result
#   See _init_session_state() for the full schema.
#
# Run with:  streamlit run app.py
# =============================================================================

from __future__ import annotations

import copy
import logging
import streamlit as st

# Internal helpers — UI components and file-loading utilities.
from utils.helper import (
    load_css,
    load_sample_code,
    render_empty_card,
    render_language_badge,
    render_placeholder,
    render_section_header,
)
import utils.gemini_client as gemini_client

# Setup module logging
logging.basicConfig(level=logging.INFO)
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


# =============================================================================
# APPLICATION METADATA
# Single source of truth for the app name, subtitle, and version.
# Use these constants everywhere (header, sidebar, footer, page title).
# =============================================================================
APP_NAME:     str = "CodeExplain"
APP_SUBTITLE: str = "Plain-English Code Tutor"
APP_VERSION:  str = "1.0.0"


# =============================================================================
# CONSTANTS
# Single source of truth for labels, icons, and tab titles.
# Changing a value here updates every place it is used in the UI.
# =============================================================================

# Default language shown in the dropdown on first load.
DEFAULT_LANGUAGE: str = "Auto Detect"

# Text shown in the spinner while the AI processes the code.
SPINNER_TEXT: str = "🤖 Analyzing your code..."

# Generic placeholder text for sections not yet populated by AI.
AI_STATUS_PLACEHOLDER: str = (
    "This section will be populated after Gemini analysis."
)

# Languages shown in the dropdown. DEFAULT_LANGUAGE must stay first (index 0).
SUPPORTED_LANGUAGES: list[str] = [
    DEFAULT_LANGUAGE,
    "Python",
    "Java",
    "C++",
    "JavaScript",
]

# Emoji icons shown beside each language name in the sidebar.
LANGUAGE_ICONS: dict[str, str] = {
    "Python":     "🐍",
    "Java":       "☕",
    "C++":        "⚙️",
    "JavaScript": "🌐",
}

# Feature bullets displayed in the sidebar.
FEATURE_LIST: list[str] = [
    "📝 Plain-English explanations",
    "🔍 Line-by-line breakdown",
    "📊 Complexity analysis",
    "💡 Code improvement tips",
    "🐛 Bug detection",
    "🧩 Interactive quiz",
    "🎓 Learning tips",
    "📄 Downloadable reports",
]

# Tab title constants — defined once so render_output_tabs() and any future
# deep-link / routing logic always share the same strings.
TAB_SUMMARY:       str = "📝 Summary"
TAB_LINEBY:        str = "🔍 Line-by-Line"
TAB_COMPLEXITY:    str = "📊 Complexity"
TAB_IMPROVEMENT:   str = "💡 Improvements"
TAB_BUGS:          str = "🐛 Bugs"
TAB_QUIZ:          str = "🧩 Quiz"
TAB_LEARNING:      str = "🎓 Learning Tips"

# Ordered list consumed by st.tabs() — display order is controlled here.
ALL_TABS: list[str] = [
    TAB_SUMMARY,
    TAB_LINEBY,
    TAB_COMPLEXITY,
    TAB_IMPROVEMENT,
    TAB_BUGS,
    TAB_QUIZ,
    TAB_LEARNING,
]


# =============================================================================
# SESSION STATE INITIALISATION
# =============================================================================
# All AI output is consolidated into ONE structured dict:
#   st.session_state.analysis_result
#
# Phase 3 hook-up guide — which module writes each field:
#   analysis_result["language"]      ← utils.language_detector
#   analysis_result["summary"]       ← utils.gemini_client + utils.prompts
#   analysis_result["line_by_line"]  ← utils.gemini_client + utils.prompts
#   analysis_result["complexity"]    ← utils.analysis
#   analysis_result["improvements"]  ← utils.gemini_client + utils.prompts
#   analysis_result["bugs"]          ← utils.gemini_client + utils.prompts
#   analysis_result["quiz"]          ← utils.quiz_generator
#   analysis_result["learning_tips"] ← utils.gemini_client + utils.prompts
#   analysis_result["report_path"]   ← utils.report_generator
#
# st.session_state.quiz_score is kept separate because it tracks live user
# interaction, not an AI response.
# =============================================================================

#: Schema for the single analysis result object stored in session state.
_ANALYSIS_RESULT_SCHEMA: dict = {
    "language":     None,   # str  — detected / selected language
    "summary":      None,   # str  — plain-English overview from Gemini
    "line_by_line": [],     # list[tuple[str, str, str]] — (label, code, explanation)
    "complexity": {
        "time":        None,  # str  — e.g. "O(2ⁿ)"
        "space":       None,  # str  — e.g. "O(n)"
        "readability": None,  # int  — score out of 10
        "difficulty":  None,  # str  — "Beginner" / "Intermediate" / "Advanced"
        "nesting_depth": None,  # int
    },
    "improvements": [],     # list[str] — improvement suggestion strings
    "bugs":         [],     # list[dict] — {severity, description, fix}
    "quiz":         [],     # list[dict] — {question, options, answer, explanation}
    "learning_tips": [],    # list[str] — concepts, topics, exercises, next steps
    "report_path":  None,   # str  — absolute path to the generated PDF/HTML
}


def _init_session_state() -> None:
    """
    Initialise all session-state keys used by the application.

    Called once at the top of ``main()``.  Keys are set only when absent
    so existing values are never overwritten on re-runs.

    State layout:
      ``st.session_state.analysis_result`` — single structured dict holding
          every AI response field (see ``_ANALYSIS_RESULT_SCHEMA`` for schema).
      ``st.session_state.quiz_score``       — running count of correct answers.
    """
    if "analysis_result" not in st.session_state:
        # Deep-copy the schema so mutating session state never affects the
        # template dict.
        st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)

    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> None:
    """
    Render the left sidebar containing:
      - Logo and project title (from APP_NAME / APP_SUBTITLE constants)
      - Supported-languages list
      - Feature highlights
      - About blurb and version tag (from APP_VERSION constant)
    """
    with st.sidebar:

        # ── Logo & branding ───────────────────────────────────────────────────
        try:
            st.image("assets/logo.png", width="stretch")
        except Exception:
            st.markdown("## 🤖")

        st.markdown(f"## {APP_NAME}")
        st.markdown(f"**{APP_SUBTITLE}** powered by Google Gemini AI.")

        st.divider()

        # ── Supported languages ───────────────────────────────────────────────
        st.markdown("### 🌐 Supported Languages")
        for lang, icon in LANGUAGE_ICONS.items():
            st.markdown(f"- {icon} **{lang}**")

        st.divider()

        # ── Feature list ──────────────────────────────────────────────────────
        st.markdown("### ✨ Features")
        for feature in FEATURE_LIST:
            st.markdown(f"- {feature}")

        st.divider()

        # ── About ─────────────────────────────────────────────────────────────
        st.markdown("### ℹ️ About")
        st.info(
            f"{APP_NAME} helps students and developers understand "
            "code snippets in plain, simple English — no jargon needed!"
        )

        st.markdown(
            f"<small>🔖 v{APP_VERSION} &nbsp;|&nbsp; Built with Streamlit</small>",
            unsafe_allow_html=True,
        )


# =============================================================================
# HERO HEADER
# =============================================================================

def render_header() -> None:
    """
    Render the centred page title and subtitle at the top of the main area.
    Title and subtitle text come from the APP_NAME / APP_SUBTITLE constants.
    """
    st.markdown(
        f"<h1 style='text-align:center;'>🤖 {APP_NAME}</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<p class='hero-subtitle'>"
        f"Your <strong>{APP_SUBTITLE}</strong> — "
        f"paste any code and instantly understand it."
        f"</p>",
        unsafe_allow_html=True,
    )
    st.divider()


# =============================================================================
# CODE INPUT SECTION
# =============================================================================

def render_input_section() -> tuple[str, str, bool]:
    """
    Render the code-paste area, language dropdown, Explain, and Clear buttons.

    The text area is pre-filled with the Python sample code on first load.
    When Clear is pressed the text area is emptied via session-state reset.

    Returns:
        code         – The raw code string currently in the text area.
        language     – The language selected in the dropdown.
        explain_btn  – ``True`` if the "Explain Code" button was clicked.
    """
    st.markdown("### 📋 Paste Your Code")

    # Use session state so the Clear button can wipe the value across reruns.
    selected_language: str = st.session_state.get("language_select", DEFAULT_LANGUAGE)
    default_code: str = st.session_state.get(
        "code_input",
        load_sample_code(selected_language),
    )

    # ── Code text area ────────────────────────────────────────────────────────
    code: str = st.text_area(
        label="Code Input",
        value=default_code,
        height=280,
        placeholder="Paste your Python, Java, C++, or JavaScript code here…",
        label_visibility="collapsed",
        key="code_input",
    )

    # ── Controls row: language selector | Explain | Clear ────────────────────
    col_lang, col_btn, col_clear = st.columns([2, 1.5, 1])

    with col_lang:
        language: str = st.selectbox(
            label="🔤 Programming Language",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(DEFAULT_LANGUAGE),
            key="language_select",
        )

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)  # vertical alignment spacer
        explain_btn: bool = st.button(
            "🚀 Explain Code",
            type="primary",
            width="stretch",
            key="explain_btn",
        )

    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🗑️ Clear",
            type="secondary",
            width="stretch",
            key="clear_btn",
        ):
            st.session_state["code_input"] = ""
            if "has_analyzed" in st.session_state:
                st.session_state.has_analyzed = False
            st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)
            st.rerun()

    return code, language, explain_btn


# =============================================================================
# INPUT VALIDATION
# =============================================================================

def validate_input(code: str) -> bool:
    """
    Validate user-supplied code before attempting any processing.

    Currently checks for non-empty input.  Add further rules (max length,
    disallowed characters, etc.) here without touching any other module.

    Args:
        code: The raw string from the text area.

    Returns:
        ``True`` if valid; ``False`` and shows a warning otherwise.
    """
    if not code.strip():
        st.warning("⚠️ Please paste some code before clicking **Explain Code**.")
        return False
    return True


# =============================================================================
# INDIVIDUAL TAB RENDERERS
# Each function owns exactly one tab's content.
# Reads real data from st.session_state.analysis_result.
# =============================================================================

def render_summary_tab(code: str) -> None:
    """
    Tab 1 — Plain-English Summary.

    Reads ``st.session_state.analysis_result["summary"]`` and
    difficulty to populate the text and metric cards below.
    """
    result = st.session_state.analysis_result
    render_section_header("📝 Plain-English Summary")
    
    summary_text = result.get("summary")
    if not summary_text:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    st.markdown(summary_text)

    # Dynamic line and definitions calculations for metrics
    raw_lines = code.splitlines()
    lines_count = len([l for l in raw_lines if l.strip()])
    def_count = sum(1 for line in raw_lines if any(kw in line for kw in ["def ", "function ", "class ", "void ", "fn "]))

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="📏 Lines of Code", value=str(lines_count))
    with col2:
        st.metric(label="🔢 Functions/Classes Found", value=str(def_count))
    with col3:
        difficulty = result.get("complexity", {}).get("difficulty", "Beginner")
        st.metric(label="⭐ Difficulty Level", value=difficulty)


def render_linebyline_tab() -> None:
    """
    Tab 2 — Line-by-Line Explanation.

    Iterates over ``st.session_state.analysis_result["line_by_line"]``
    — a list of ``(label, code_line, explanation)`` tuples.
    """
    result = st.session_state.analysis_result
    render_section_header("🔍 Line-by-Line Explanation")
    
    rows = result.get("line_by_line", [])
    if not rows:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    # Determine highlight language configuration dynamically
    lang = str(result.get("language", "python")).lower()
    lang_highlight = "python"
    if "javascript" in lang:
        lang_highlight = "javascript"
    elif "c++" in lang or "cpp" in lang:
        lang_highlight = "cpp"
    elif "java" in lang:
        lang_highlight = "java"

    for label, code_line, explanation in rows:
        with st.container(border=True):
            col_code, col_exp = st.columns([1, 2])
            with col_code:
                st.code(code_line, language=lang_highlight)
            with col_exp:
                st.markdown(f"**{label}:** {explanation}")


def render_complexity_tab() -> None:
    """
    Tab 3 — Complexity Analysis.

    Reads ``st.session_state.analysis_result["complexity"]`` — a dict with
    keys ``time``, ``space``, ``readability``, ``difficulty``, and
    ``nesting_depth``.
    """
    result = st.session_state.analysis_result
    render_section_header("📊 Complexity Analysis")
    
    complexity = result.get("complexity", {})
    if not complexity or complexity.get("time") is None:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**🕐 Algorithmic Complexity**")
        st.metric(label="Time Complexity", value=complexity.get("time", "N/A"))
        st.metric(label="Space Complexity", value=complexity.get("space", "N/A"))
    with col_right:
        st.markdown("**📐 Code Metrics**")
        st.metric(label="Max Nesting Depth", value=str(complexity.get("nesting_depth", "N/A")))
        st.metric(label="Readability Score", value=f"{complexity.get('readability', 'N/A')}/10")
        st.metric(label="Difficulty Rating", value=complexity.get("difficulty", "N/A"))


def render_improvement_tab() -> None:
    """
    Tab 4 — Suggested Improvements.

    Iterates over ``st.session_state.analysis_result["improvements"]``
    — a list of improvement strings.
    """
    result = st.session_state.analysis_result
    render_section_header("💡 Suggested Improvements")
    
    improvements = result.get("improvements", [])
    if not improvements:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    for idx, imp in enumerate(improvements, start=1):
        render_empty_card(imp, icon="✅")


def render_bug_tab() -> None:
    """
    Tab 5 — Potential Bugs & Issues.

    Iterates over ``st.session_state.analysis_result["bugs"]``
    — a list of dicts with keys ``severity``, ``description``, and ``fix``.
    """
    result = st.session_state.analysis_result
    render_section_header("🐛 Potential Bugs & Issues")
    
    bugs = result.get("bugs", [])
    if not bugs:
        # Gracefully handle the no-bugs state with positive educational reinforcement
        st.success("🎉 No bugs, anti-patterns, or logic errors were identified in this code!")
        return

    # Determine highlight language configuration dynamically
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
        
        box_text = f"**Issue {idx} ({severity.capitalize()} Severity):** {desc}"
        
        with st.container(border=True):
            if "high" in severity:
                st.error(box_text)
            elif "medium" in severity:
                st.warning(box_text)
            else:
                st.info(box_text)
                
            if fix.strip():
                st.markdown("**Suggested Fix:**")
                st.code(fix, language=lang_highlight)


def render_quiz_tab() -> None:
    """
    Tab 6 — Comprehension Quiz.

    Iterates over ``st.session_state.analysis_result["quiz"]`` — a list
    of question dicts. Tracks score dynamically using persistent radio keys.
    """
    result = st.session_state.analysis_result
    render_section_header("🧩 Comprehension Quiz")
    
    quiz_questions = result.get("quiz", [])
    if not quiz_questions:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    correct_answers = 0
    total_questions = len(quiz_questions)
    answered_questions = 0

    for idx, q in enumerate(quiz_questions):
        st.markdown(f"##### Q{idx+1}. {q.get('question')}")
        
        options = q.get("options", [])
        correct_answer = q.get("answer", "")
        explanation = q.get("explanation", "")
        
        # Unique key for persistent selections
        user_choice = st.radio(
            label=f"q_{idx}_label",
            options=options,
            index=None,
            key=f"quiz_q_{idx}",
            label_visibility="collapsed"
        )
        
        if user_choice:
            answered_questions += 1
            if user_choice == correct_answer:
                correct_answers += 1
                st.success(f"✅ **Correct!** {explanation}")
            else:
                st.error(f"❌ **Incorrect.** The correct answer is: **{correct_answer}**\n\n{explanation}")
        st.markdown("---")

    # Update state score
    st.session_state.quiz_score = correct_answers

    col_score, col_submit = st.columns([3, 1])
    with col_score:
        st.markdown(f"### 📊 Score: **{correct_answers}** / **{total_questions}** questions answered")
    with col_submit:
        all_done = (answered_questions == total_questions)
        if st.button("📤 Submit Quiz", disabled=not all_done, width="stretch", key="submit_quiz"):
            if correct_answers == total_questions:
                st.balloons()
                st.success("🏆 Perfect Score! Excellent understanding of the code snippet!")
            else:
                st.info("👍 Quiz submitted successfully! Review the incorrect options to learn more.")


def render_learning_tab() -> None:
    """
    Tab 7 — Learning Tips.

    Iterates over ``st.session_state.analysis_result["learning_tips"]``
    — a list of tip strings covering practice exercises, topics, and tasks.
    """
    result = st.session_state.analysis_result
    render_section_header("🎓 Learning Tips")
    
    tips = result.get("learning_tips", [])
    if not tips:
        render_placeholder(AI_STATUS_PLACEHOLDER)
        return

    st.markdown("##### 📚 Recommended Tips & Topics")
    for tip in tips:
        # Determine standard category icons based on contents dynamically
        icon = "💡"
        tip_lower = tip.lower()
        if "recursion" in tip_lower or "loop" in tip_lower:
            icon = "🔁"
        elif "complexity" in tip_lower or "big-o" in tip_lower:
            icon = "📊"
        elif "practice" in tip_lower or "rewrite" in tip_lower:
            icon = "🏋️"
        elif "explore" in tip_lower or "read" in tip_lower:
            icon = "🧭"
            
        render_empty_card(tip, icon=icon)


# =============================================================================
# OUTPUT TAB ORCHESTRATOR
# =============================================================================

def render_output_tabs(code: str, language: str) -> None:
    """
    Orchestrate all seven analysis-result tabs.

    This function only creates the tab containers from ``ALL_TABS`` and
    delegates all content rendering to the individual ``render_*_tab()``
    functions.  To change tab order or add a new tab, update ``ALL_TABS``
    and add/reorder the ``with tab_*`` blocks below.

    Args:
        code:     The user's code snippet (stored for future AI processing).
        language: The detected / selected language (stored for future use).
    """
    st.divider()
    st.markdown("### 📊 Analysis Results")
    render_language_badge(language)

    # Unpack exactly as many variables as there are entries in ALL_TABS.
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
# EMPTY STATE
# =============================================================================

def render_empty_state() -> None:
    """
    Render a centred call-to-action prompt shown before the user has
    clicked **Explain Code** for the first time in the session.
    """
    st.divider()
    st.markdown(
        "<div class='empty-state'>"
        "<h3>👆 Paste your code above and click <em>Explain Code</em></h3>"
        "<p>"
        "The AI will generate a plain-English explanation, complexity "
        "analysis, improvement tips, bug reports, and a comprehension "
        "quiz — all in seconds."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# PHASE 3 INTEGRATION POINT
# =============================================================================

def process_code(code: str, language: str) -> None:
    """
    Phase 3 integration point — orchestrates all AI analysis modules.

    Calls the single unified generate_complete_analysis() method from gemini_client
    and maps the returned values directly into st.session_state.analysis_result keys.
    If the API call fails, details are logged and fallbacks are loaded.

    Args:
        code:     The raw code string submitted by the user.
        language: The language selected in the dropdown (or auto-detected).
    """
    # 1. Reset analysis_result to baseline schema with the active language
    st.session_state.analysis_result = copy.deepcopy(_ANALYSIS_RESULT_SCHEMA)
    st.session_state.analysis_result["language"] = language

    try:
        # Single request execution
        analysis = gemini_client.generate_complete_analysis(code, language)
        
        # Load elements into state
        st.session_state.analysis_result["summary"] = analysis.get("summary", "")
        st.session_state.analysis_result["line_by_line"] = analysis.get("line_by_line", [])
        st.session_state.analysis_result["complexity"] = analysis.get("complexity", {})
        st.session_state.analysis_result["improvements"] = analysis.get("improvements", [])
        st.session_state.analysis_result["bugs"] = analysis.get("bugs", [])
        st.session_state.analysis_result["quiz"] = analysis.get("quiz", [])
        st.session_state.analysis_result["learning_tips"] = analysis.get("learning_tips", [])
        
        # Reset running quiz score
        st.session_state.quiz_score = 0
        
    except Exception as e:
        logger.error(f"Failed to process unified code analysis: {e}")
        # Retain standard baseline defaults
        st.session_state.quiz_score = 0


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================


def main() -> None:
    """
    Top-level orchestrator — initialises state then calls render functions.

    Flow:
      1. Initialise session state (single analysis_result object + quiz_score)
      2. Sidebar
      3. Hero header
      4. Code input section  →  returns (code, language, explain_clicked)
      5a. If explain_clicked and input valid → spinner + output tabs
      5b. If explain_clicked but input empty → validation warning (via validate_input)
      5c. Otherwise                          → empty-state prompt
    """
    _init_session_state()

    render_sidebar()
    render_header()

    code, language, explain_clicked = render_input_section()

    if explain_clicked:
        if validate_input(code):
            # Store the selected language immediately so all Phase 3 modules
            # can read it from session state without needing extra arguments.
            st.session_state.analysis_result["language"] = language

            with st.spinner(SPINNER_TEXT):
                process_code(code, language)

            st.session_state.has_analyzed = True
            render_output_tabs(code, language)
    elif st.session_state.get("has_analyzed", False):
        language_used = st.session_state.analysis_result.get("language", language)
        render_output_tabs(code, language_used)
    else:
        render_empty_state()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
