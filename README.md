# 🧠 CodeExplain: Plain-English Code Tutor

> An AI-powered learning tool that explains code snippets in plain English, generates interactive quizzes, and produces downloadable learning reports — powered by Google Gemini.

---

## 📖 Description

**CodeExplain** is a Streamlit-based web application designed to help beginners and intermediate developers understand code written in Python, JavaScript, Java, C++, and more.

Paste or drag-and-drop any code snippet and instantly receive:
- ✅ A plain-English, line-by-line explanation
- 🧩 Auto-generated comprehension quizzes
- 📄 Downloadable Markdown/HTML learning reports
- 🔍 Key concept identification and complexity analysis
- 🚀 **Single-Request Architecture**: All insights generated in one efficient Gemini API call.

---

## 📁 Folder Structure

```
CodeExplain/
│
├── app.py                    # Main Streamlit application entry point
├── config.py                 # Environment variables & app-wide constants
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation (this file)
├── .env.example              # Template for environment secrets
├── .gitignore                # Files & folders excluded from version control
│
├── assets/
│   ├── logo.png              # App logo / branding image
│   └── styles.css            # Custom CSS for Streamlit UI
│
├── reports/                  # Auto-generated PDF/HTML reports (git-ignored)
│
├── sample_codes/
│   ├── python_example.py     # Sample Python snippet for demos
│   ├── java_example.java     # Sample Java snippet for demos
│   ├── cpp_example.cpp       # Sample C++ snippet for demos
│   └── javascript_example.js # Sample JavaScript snippet for demos
│
├── utils/
│   ├── __init__.py           # Makes utils a Python package
│   ├── gemini_client.py      # Google Gemini API wrapper (Single-Request Architecture)
│   ├── language_detector.py  # Auto-detects programming language
│   ├── code_processor.py     # Code parsing and pre-processing
│   ├── analysis.py           # Code metrics and concept extraction
│   ├── report_generator.py   # Markdown/HTML report export
│   └── helper.py             # Shared utility functions
│
└── tests/
    └── test_language_detector.py  # Unit tests for language detection
```

---

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/CodeExplain-Plain-English-Code-Tutor.git
   cd CodeExplain-Plain-English-Code-Tutor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

### 🐳 Running with Docker

1. **Build the image**
   ```bash
   docker build -t codeexplain .
   ```

2. **Run the container**
   ```bash
   docker run -p 8501:8501 --env-file .env codeexplain
   ```

---

## 🔑 Environment Variables

| Variable         | Description                        |
|------------------|------------------------------------|
| `GEMINI_API_KEY` | Your Google Gemini API key         |

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **AI Model**: Google Gemini 2.5 Flash (via `google-generativeai`)
- **Language Detection**: Custom Heuristics
- **Report Export**: Markdown & HTML
- **Deployment**: Docker ready
- **Config Management**: python-dotenv

---

## 📜 License

MIT License — see `LICENSE` for details.