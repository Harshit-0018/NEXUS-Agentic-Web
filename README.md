# NEXUS — Agentic Web Platform
Agentic Web Theme

> An autonomous AI agent that browses, interacts, and gets things done on the web on your behalf — without hand-holding.

---

##  Project Structure

```
nexus-agent/
├── index.html                        # Main frontend (open directly in browser)
├── src/
│   ├── styles/
│   │   └── main.css                  # All styles
│   └── utils/
│       ├── agent-simulation.js       # Frontend demo simulation engine
│       ├── animations.js             # Scroll animations, counters
│       └── main.js                   # UI interactions
├── backend/
│   ├── main.py                       # FastAPI app (REST + WebSocket)
│   ├── config.py                     # Settings / env vars
│   ├── requirements.txt              # Python dependencies
│   ├── .env.example                  # Copy to .env and fill keys
│   ├── agent/
│   │   ├── core.py                   # 🧠 Main ReAct agent loop
│   │   ├── tools/
│   │   │   ├── browser.py            # Playwright browser automation
│   │   │   ├── search.py             # DuckDuckGo / Bing web search
│   │   │   ├── extractor.py          # LLM-powered data extraction
│   │   │   └── form_filler.py        # Web form automation
│   │   └── memory/
│   │       ├── session_memory.py     # Short-term context window
│   │       └── vector_store.py       # Long-term Pinecone memory
│   └── utils/
│       └── logger.py                 # Shared logger
└── README.md
```

---

##  Quick Start

### Option A — Frontend Only (No Setup Required)

Just open `index.html` in your browser. The interactive demo works fully in-browser with a simulated agent.

```bash
# If you want a local server (optional):
npx serve .
# OR
python -m http.server 5500
# Then open http://localhost:5500
```

### Option B — Full Stack (Real AI Agent)

#### 1. Clone & Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env and add your Azure OpenAI key
```

#### 2. Configure `.env`

```env
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
OPENAI_API_KEY=sk-...          # fallback if no Azure
PINECONE_API_KEY=...           # optional, for long-term memory
```

#### 3. Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

#### 4. Start Frontend

```bash
# From project root
npx serve . -p 3000
# Open http://localhost:3000
```

---

##  API Reference

### REST

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/health` | Health check |
| `POST` | `/api/run` | Start an agent task |
| `GET`  | `/api/status/{job_id}` | Poll task status |
| `DELETE` | `/api/cancel/{job_id}` | Cancel running task |

#### POST /api/run

```json
{
  "task": "Find top 5 AI startups funded in 2024",
  "mode": "autonomous",
  "max_steps": 20,
  "output_format": "json"
}
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "queued",
  "message": "Connect to /ws/agent/{job_id} for real-time stream"
}
```

### WebSocket

```javascript
const ws = new WebSocket(
  `ws://localhost:8000/ws/agent?task=Find top AI startups&max_steps=20`
);

ws.onmessage = (e) => {
  const msg = JSON.parse(e.data);
  // msg.type: "connected" | "step" | "done" | "error"
  // msg.data: AgentStep object (for type="step")
  console.log(msg);
};
```

### Python SDK Usage

```python
import asyncio
import httpx

async def run_task():
    async with httpx.AsyncClient() as client:
        # Start task
        r = await client.post("http://localhost:8000/api/run", json={
            "task": "Compare iPhone 16 Pro prices across Amazon and Flipkart",
            "mode": "autonomous",
            "max_steps": 15
        })
        job = r.json()
        job_id = job["job_id"]

        # Poll for result
        while True:
            status = await client.get(f"http://localhost:8000/api/status/{job_id}")
            data = status.json()
            if data["status"] in ("complete", "failed", "partial"):
                print(data["result"])
                break
            await asyncio.sleep(2)

asyncio.run(run_task())
```

---

##  Architecture

```
User Input (Natural Language)
          ↓
   Task Decomposer
          ↓
   LLM Planner (Azure GPT-4o)
   ┌──────────────────────────┐
   │  ReAct Loop (max N steps)│
   │  THINK → ACT → OBSERVE  │
   └──────────────────────────┘
          ↓
   Tool Execution Layer
   ┌─────────┬──────────┬──────────┬───────────┐
   │ Browser │  Search  │ Extract  │ FormFill  │
   │Playwright│DuckDuckGo│ LLM+BS4 │ Playwright│
   └─────────┴──────────┴──────────┴───────────┘
          ↓
   Memory Layer
   ┌──────────────────┬──────────────────┐
   │  Session Memory  │  Vector Memory   │
   │  (context window)│  (Pinecone DB)   │
   └──────────────────┴──────────────────┘
          ↓
   Structured Output + Execution Trace


```
## Architecture Workflow

<img width="1360" height="1840" alt="image" src="https://github.com/user-attachments/assets/30cf8f80-6dfa-4c30-ab40-221460da6f84" />

---

## Live Demo

### Frontpage(Start)
<img width="1914" height="908" alt="image" src="https://github.com/user-attachments/assets/290a54f8-f675-4689-a544-092fd5a65243" />

### Watch Nexus Work
<img width="1918" height="911" alt="image" src="https://github.com/user-attachments/assets/a071391d-2efa-4280-969c-a48a8d3043f3" />

### How Nexus Work
<img width="1918" height="891" alt="image" src="https://github.com/user-attachments/assets/ff9b7cb7-ade8-401f-a4db-b0d0b630b2b1" />

### Built for Real Problems
<img width="1912" height="837" alt="image" src="https://github.com/user-attachments/assets/bfc39f8d-0e7d-4ff3-b396-35528a4fea31" />

### Docs
<img width="1917" height="904" alt="image" src="https://github.com/user-attachments/assets/fda275df-ecaf-48c4-bdb2-167df12df049" />

---


### Key Design Decisions

**ReAct Loop**: The agent uses Reasoning + Acting (ReAct) — at each step it thinks, then acts, then observes the result. This allows dynamic replanning.

**Error Recovery**: If a tool fails, the agent catches the error, appends it to context, and the LLM replans automatically.

**Streaming**: WebSocket streams each step as it happens — no waiting for full completion.

**Memory**: Session memory prevents loops; vector memory avoids redoing work across sessions.

---

##  Supported Task Types

| Category | Example Task |
|----------|-------------|
| Research | "Find top 10 open-source LLM projects on GitHub with stars" |
| Shopping | "Compare laptop prices under ₹60,000 across Amazon and Flipkart" |
| Travel | "Find cheapest Delhi → Mumbai flights this weekend" |
| News | "Summarize latest Azure AI announcements this week" |
| Data | "Extract all speaker names and topics from this conference page" |
| Forms | "Fill in my profile on LinkedIn with these details" |

---

##  Safety Features

- **Read-only mode**: Agent can only read/extract, never submit forms
- **Supervised mode**: Agent pauses for human approval before each action
- **Domain allowlist**: Restrict which domains the agent can visit
- **Max steps cap**: Prevents runaway agent loops
- **Timeout**: Hard timeout kills any stuck task

---

##  Notes

**Theme**: Agentic Web — Build autonomous agents that navigate websites, extract information, complete transactions, and orchestrate actions across services.

**What makes NEXUS stand out**:
1. **Real browser automation** — Not just API calls; actual Playwright browser
2. **Resilient recovery** — Replans automatically on failure
3. **Memory across sessions** — Vector DB for long-term recall
4. **Real-time trace** — Full transparency into agent reasoning
5. **Multi-modal** — Can process text and screenshots

**Built with**: Azure OpenAI, Playwright, FastAPI, LangChain, Pinecone, WebSockets

---

## 📝 License

Harshit !
