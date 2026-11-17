# 🎯 JobHunt Agent Squad

A multi-agent system (CrewAI) that hunts jobs for you:
**Scraper → Matcher → Tailor → Tracker**, running as one crew.

## Architecture

```
Target role + Resume
      │
      ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 1. Scraper    │──▶│ 2. Matcher    │──▶│ 3. Tailor     │──▶│ 4. Tracker    │
│ fetch live    │   │ score resume  │   │ cover letter  │   │ log to CSV    │
│ jobs (Remotive│   │ fit 0–100,    │   │ + resume      │   │ tracker       │
│ API)          │   │ keep top N    │   │ bullets       │   │               │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env        # then add your GROQ_API_KEY (free: console.groq.com)

# CLI
python main.py "python developer" data/resume_sample.txt

# Web UI
streamlit run app.py
```

## LLM options
- **Groq** (free tier): set `GROQ_API_KEY`, default model `groq/llama-3.3-70b-versatile`
- **OpenRouter**: set `OPENROUTER_API_KEY` and change `MODEL` in `.env`

## Outputs
- `outputs/tailored_applications.md` — cover letters + tailored resume bullets per job
- `outputs/applications_log.csv` — tracker log of every application

## Interview talking points
- "Why multi-agent?" → separation of concerns, each agent has one clear role,
  easy to swap/mock/test individually, human-readable pipeline.
- "What about hallucinated jobs?" → scraper returns structured JSON from a real
  API with a typed fallback; matcher only scores what the scraper returned.
- "How would you scale it?" → swap CSV for Postgres, add LangGraph for
  conditional loops, add human-in-the-loop approval before "applying".

## Deploy
Streamlit → free on **HuggingFace Spaces** or **Streamlit Community Cloud**
(set secrets = your `.env` contents). Perfect live-demo link for your resume.
