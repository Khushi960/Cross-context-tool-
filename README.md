# Context Bridge

Write a project's state once, then paste a handoff into Claude, ChatGPT or Gemini and continue without re-explaining.

- **frontend/**  React + TypeScript (Vite). Notion-style pages, autosave, live handoff preview.
- **backend/**   FastAPI + SQLite. Stores packets, formats handoffs, and calls an LLM (Anthropic API) to fill a packet from a pasted chat or to condense a long transcript.
- **frontend/dist/**  A prebuilt copy of the frontend. The backend serves it, so you do not need Node to run the app.

## Run (Python only)

    cd backend
    python3 -m pip install -r requirements.txt
    cp .env.example .env          # then paste your ANTHROPIC_API_KEY into .env
    python3 -m uvicorn app.main:app --reload

Open http://127.0.0.1:8000

The app works without an API key. Only "Fill from chat" and "Condense with AI" need one.

## Develop the frontend (needs Node 18+)

    cd frontend
    npm install
    npm run dev                    # http://localhost:5173, proxies /api to port 8000
    npm run build                  # rebuilds frontend/dist

## API (docs at /docs)

| Method | Path | What it does |
|---|---|---|
| GET | /api/health | Server status and whether an API key is set |
| GET, POST | /api/packets | List or create packets |
| GET, PUT, DELETE | /api/packets/{id} | Read, save or delete one packet |
| POST | /api/extract | LLM reads a chat transcript and returns packet fields |
| POST | /api/handoff | Formats a packet for claude, chatgpt or gemini within a token limit |

## How it works

1. A packet holds goal, status, decisions, constraints, facts, open questions, answer style and recent chat.
2. `formatting.py` renders it per tool: XML tags for Claude, Markdown for ChatGPT, plain sections for Gemini.
3. Tokens are estimated as characters / 4. If the chat is too long it is trimmed from the top, or the LLM condenses it.
4. `llm.py` holds every model call. Set CONTEXT_BRIDGE_MODEL in .env to change the model.
