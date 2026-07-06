# =============================================================================
# utils/report_generator.py — Report Export
# =============================================================================
# Generates downloadable learning reports for users, containing:
#   - The submitted code snippet
#   - The plain-English explanation produced by the AI
#   - Complexity, bugs, improvements, and learning tips
#
# Supports export formats: Markdown and HTML.
# =============================================================================

import html
from typing import Any

def generate_markdown_report(result: dict[str, Any], code: str) -> str:
    """Generate a formatted Markdown report from the analysis result."""
    lang = result.get("language", "Code")
    summary = result.get("summary", "No summary available.")
    
    md = f"# CodeExplain Report\n\n"
    md += f"## Source Code ({lang})\n"
    md += f"```\n{code}\n```\n\n"
    
    md += f"## Summary\n{summary}\n\n"
    
    md += f"## Complexity\n"
    comp = result.get("complexity", {})
    md += f"- **Time**: {comp.get('time', 'N/A')}\n"
    md += f"- **Space**: {comp.get('space', 'N/A')}\n"
    md += f"- **Difficulty**: {comp.get('difficulty', 'N/A')}\n"
    md += f"- **Readability**: {comp.get('readability', 'N/A')}/10\n\n"
    
    md += f"## Line-by-Line\n"
    for label, c_line, exp in result.get("line_by_line", []):
        md += f"**{label}**: `{c_line}`\n> {exp}\n\n"
        
    md += f"## Improvements\n"
    improvements = result.get("improvements", [])
    if improvements:
        for imp in improvements:
            md += f"- {imp}\n"
    else:
        md += "No improvements suggested.\n"
    md += "\n"
    
    md += f"## Bugs\n"
    bugs = result.get("bugs", [])
    if not bugs:
        md += "No bugs detected.\n\n"
    else:
        for b in bugs:
            md += f"- **{b.get('severity', 'Medium')}**: {b.get('description', '')}\n"
            if b.get('fix'):
                md += f"  - Fix: `{b.get('fix')}`\n"
        md += "\n"
        
    md += f"## Learning Tips\n"
    tips = result.get("learning_tips", [])
    if tips:
        for tip in tips:
            md += f"- {tip}\n"
    else:
        md += "No tips available.\n"
        
    return md

def generate_html_report(result: dict[str, Any], code: str) -> str:
    """Generate a simple, self-contained HTML report."""
    lang = html.escape(result.get("language", "Code"))
    summary = html.escape(result.get("summary", "No summary available."))
    
    html_out = f"<html><head><meta charset='utf-8'><title>CodeExplain Report</title>"
    html_out += "<style>"
    html_out += "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; padding: 30px; max-width: 900px; margin: 0 auto; color: #333; line-height: 1.6; }"
    html_out += "h1, h2 { color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 10px; }"
    html_out += "pre { background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #e9ecef; }"
    html_out += "code { font-family: Consolas, 'Courier New', monospace; background: #f8f9fa; padding: 2px 5px; border-radius: 3px; border: 1px solid #e9ecef; }"
    html_out += "ul { padding-left: 20px; }"
    html_out += "li { margin-bottom: 10px; }"
    html_out += ".label { font-weight: bold; color: #0366d6; }"
    html_out += "</style></head><body>"
    
    html_out += f"<h1>CodeExplain Report</h1>"
    
    html_out += f"<h2>Source Code ({lang})</h2>"
    html_out += f"<pre><code>{html.escape(code)}</code></pre>"
    
    html_out += f"<h2>Summary</h2>"
    html_out += f"<p>{summary}</p>"
    
    html_out += f"<h2>Complexity</h2>"
    comp = result.get("complexity", {})
    html_out += f"<ul>"
    html_out += f"<li><strong>Time</strong>: {html.escape(str(comp.get('time', 'N/A')))}</li>"
    html_out += f"<li><strong>Space</strong>: {html.escape(str(comp.get('space', 'N/A')))}</li>"
    html_out += f"<li><strong>Difficulty</strong>: {html.escape(str(comp.get('difficulty', 'N/A')))}</li>"
    html_out += f"<li><strong>Readability</strong>: {html.escape(str(comp.get('readability', 'N/A')))}/10</li>"
    html_out += f"</ul>"
    
    html_out += f"<h2>Line-by-Line</h2>"
    html_out += f"<ul>"
    for label, c_line, exp in result.get("line_by_line", []):
        html_out += f"<li><span class='label'>{html.escape(str(label))}</span>: <code>{html.escape(str(c_line))}</code><br>{html.escape(str(exp))}</li>"
    html_out += f"</ul>"
    
    html_out += f"<h2>Improvements</h2>"
    improvements = result.get("improvements", [])
    if improvements:
        html_out += f"<ul>"
        for imp in improvements:
            html_out += f"<li>{html.escape(str(imp))}</li>"
        html_out += f"</ul>"
    else:
        html_out += "<p>No improvements suggested.</p>"
        
    html_out += f"<h2>Bugs</h2>"
    bugs = result.get("bugs", [])
    if not bugs:
        html_out += "<p>No bugs detected.</p>"
    else:
        html_out += f"<ul>"
        for b in bugs:
            sev = html.escape(str(b.get('severity', 'Medium')))
            desc = html.escape(str(b.get('description', '')))
            fix = str(b.get('fix', ''))
            html_out += f"<li><strong>{sev}</strong>: {desc}"
            if fix:
                html_out += f"<br>Fix: <code>{html.escape(fix)}</code>"
            html_out += f"</li>"
        html_out += f"</ul>"
        
    html_out += f"<h2>Learning Tips</h2>"
    tips = result.get("learning_tips", [])
    if tips:
        html_out += f"<ul>"
        for tip in tips:
            html_out += f"<li>{html.escape(str(tip))}</li>"
        html_out += f"</ul>"
    else:
        html_out += "<p>No tips available.</p>"
        
    html_out += "</body></html>"
    return html_out
