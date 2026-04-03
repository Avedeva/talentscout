# 🎯 TalentScout — AI Hiring Assistant

An intelligent hiring assistant chatbot built for TalentScout, a fictional tech recruitment agency. It screens candidates by gathering essential information and generating tailored technical interview questions based on their declared tech stack.

---

## Features

- **Guided conversation flow** — structured state machine moves candidates through 8 stages seamlessly
- **Dynamic technical questions** — 3–5 questions generated per candidate, tailored to their exact tech stack
- **Privacy-first data storage** — emails and phone numbers are masked before being written to disk
- **Polished dark UI** — custom Streamlit CSS with DM Serif/Sans/Mono typography
- **Fallback handling** — off-topic inputs are redirected; exit keywords gracefully end the session
- **Live candidate sidebar** — shows current candidate info + history of past sessions

---

## Project Structure

```
talentscout/
├── app.py              # Streamlit entry point and UI
├── conversation.py     # State machine, LLM calls, stage routing
├── prompts.py          # All prompt templates (system + per-stage)
├── data_handler.py     # Data collection, validation, masking, JSON storage
├── requirements.txt
├── .env                # Your API key (not committed)
└── candidate_data/     # Auto-created; stores masked candidate JSON files
```

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/talentscout-hiring-assistant
cd talentscout-hiring-assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

Create a `.env` file (or set the environment variable directly):

```bash
# Option A: shell export
export ANTHROPIC_API_KEY="sk-ant-..."

# Option B: .env file (add python-dotenv to requirements.txt and load it in app.py)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

> The app uses the **Anthropic Claude** API (`claude-sonnet-4-20250514`). Get a key at https://console.anthropic.com

### 5. Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Usage Guide

1. The assistant (Alex) greets you automatically.
2. Answer each question naturally — no need to use special formats.
3. After sharing your tech stack, Alex will ask 5 technical questions.
4. Type **"bye"**, **"exit"**, **"done"**, or **"quit"** at any point to end gracefully.
5. Your profile is saved (masked) to `candidate_data/`.

---

## Technical Details

| Component | Choice | Reason |
|---|---|---|
| LLM | Claude (`claude-sonnet-4-20250514`) | Strong instruction-following, fast, cost-effective |
| Frontend | Streamlit | Quick to ship, supports custom CSS |
| State | `st.session_state` | Simple, no DB needed for single-user demo |
| Storage | Local JSON | GDPR-friendly (masked), zero infra |

### Architecture

```
User (browser)
    ↓ HTTP
Streamlit (app.py)          ← UI rendering, session state
    ↓
ConversationManager         ← Stage routing, history management
    ├── prompts.py          ← System + stage instructions
    ├── Anthropic API       ← Claude for responses + question generation
    └── data_handler.py     ← Extraction, validation, masked storage
```

---

## Prompt Design

### System prompt
Sets the persona (Alex, TalentScout recruiter), enforces strict topic constraints, and defines tone. Injected on every API call so the model never loses context.

### Stage instructions
Each stage has a targeted instruction appended to the system prompt. This tells the model exactly what to do at that moment — e.g., "ask for email, validate format, move on". Stage instructions are short (5–8 lines) and use imperative language.

### Technical question generation
A separate API call with a structured prompt requests a Python list of `N` questions covering the declared tech stack. The response is parsed with `ast.literal_eval` with a regex fallback. Questions are then asked one at a time in subsequent turns, injected as a hint in the system prompt so the LLM phrases them naturally.

### Fallback
The system prompt instructs the model to redirect off-topic messages. Exit keywords are detected client-side (no LLM call needed) for reliability.

---

## Data Privacy

- Emails stored as `j***.d**@gmail.com` — original never written to disk
- Phone numbers stored with middle digits masked
- No plain-text PII in logs
- Candidate data stored locally; in production, encrypt at rest and implement a deletion endpoint (GDPR Art. 17)

---

## Challenges & Solutions

| Challenge | Solution |
|---|---|
| LLM drifting off-topic | Strong system prompt + per-stage instructions keep context tight |
| Parsing LLM-generated question lists | `ast.literal_eval` + regex fallback + hardcoded safety net |
| Email validation from freeform text | Regex extraction before passing to LLM |
| Streamlit re-running on every interaction | `st.session_state` preserves manager instance across reruns |
| Context window management | Trim history to last 20 messages before each API call |

---

## Optional Enhancements (Bonus)

- **Sentiment analysis**: Add `textblob` and display a live emoji mood indicator in the sidebar
- **Multilingual**: Add a language selector; prepend `"Respond in {lang}."` to the system prompt
- **Cloud deploy**: Push to [Streamlit Community Cloud](https://streamlit.io/cloud) (free) — just add `ANTHROPIC_API_KEY` as a secret

---

## License

MIT — for educational/demo purposes.
