# CodeExplain: Plain-English Code Tutor

CodeExplain is a Streamlit-based application that helps students and developers understand source code in plain English. It accepts pasted code or uploaded source files, sends a single Gemini analysis request, and returns a structured explanation with statistics, complexity details, bug insights, quiz questions, learning tips, and downloadable reports.

## Overview

- Explain code in clear, beginner-friendly language
- Support Python, Java, JavaScript, C++, and Auto Detect
- Provide line-by-line analysis, complexity insights, and improvement suggestions
- Generate downloadable Markdown, HTML, and JSON reports
- Keep a lightweight session history and analytics experience

## Features

- File upload and direct code paste
- Manual language selection or automatic detection
- Summary, line-by-line breakdown, complexity analysis, bug review, quiz, and learning tips
- Downloadable analysis reports
- Session analytics and recent history

## Technology Stack

- Streamlit for the web interface
- Google Gemini for AI-powered analysis
- Python standard library for processing and reporting

## Architecture

The project uses a single-request analysis flow:

1. The app collects user input from the editor or file uploader.
2. The input is validated and prepared.
3. A single Gemini request produces the full analysis payload.
4. The app renders the results in the analysis tabs and download area.

## Installation

```bash
pip install -r requirements.txt
```

## How to Run

```bash
streamlit run app.py
```

## Folder Structure

```text
CodeExplain-Plain-English-Code-Tutor/
├── app.py
├── config.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── assets/
│   ├── logo.png
│   └── styles.css
├── reports/
├── utils/
│   ├── analysis.py
│   ├── code_processor.py
│   ├── gemini_client.py
│   ├── helper.py
│   ├── language_detector.py
│   ├── report_generator.py
│   └── __init__.py
└── tests/
```

## Screenshots

The app presents a minimal landing page with:
- a title and subtitle
- an upload control and code editor
- a language selector
- an explain button

## Future Scope

- Additional export formats
- More refined quiz and learning experiences
- Expanded educational content and onboarding

## License

MIT License