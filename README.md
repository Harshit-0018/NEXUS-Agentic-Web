# NEXUS — Agentic Web Platform
### Microsoft Hackathon 2025 | Agentic Web Theme

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
<svg width="1360" viewBox="0 0 680 920" xmlns="http://www.w3.org/2000/svg" style="background:#0c1020;font-family:'Segoe UI',system-ui,sans-serif">

  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M2 1L8 5L2 9" fill="none" stroke="context-stroke" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>

  <!-- BG grid lines subtle -->
  <rect width="680" height="920" fill="#0c1020"/>

  <!-- LAYER LABELS -->
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,88) rotate(-90)">USER</text>
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,220) rotate(-90)">FRONTEND</text>
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,370) rotate(-90)">API</text>
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,530) rotate(-90)">AGENT</text>
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,680) rotate(-90)">TOOLS</text>
  <text font-size="10" fill="#ffffff22" text-anchor="start" transform="translate(10,840) rotate(-90)">MEMORY</text>

  <!-- ── USER ── -->
  <rect x="240" y="30" width="200" height="56" rx="10" fill="#1e2535" stroke="#4a5568" stroke-width="0.8"/>
  <text font-size="14" font-weight="600" fill="#e2e8f0" text-anchor="middle" x="340" y="55">User</text>
  <text font-size="12" fill="#94a3b8" text-anchor="middle" x="340" y="74">Natural language task</text>

  <line x1="340" y1="86" x2="340" y2="136" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text font-size="11" fill="#64748b" x="352" y="114">HTTP / WS</text>

  <!-- ── FRONTEND ── -->
  <rect x="60" y="136" width="560" height="120" rx="14" fill="#1a1f35" stroke="#534AB7" stroke-width="1"/>
  <text font-size="14" font-weight="600" fill="#AFA9EC" text-anchor="middle" x="340" y="162">Frontend — index.html</text>

  <rect x="80" y="172" width="148" height="68" rx="8" fill="#26215C" stroke="#534AB7" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#CECBF6" text-anchor="middle" x="154" y="198">Task Input UI</text>
  <text font-size="11" fill="#7F77DD" text-anchor="middle" x="154" y="216">Presets, config, run</text>

  <rect x="246" y="172" width="148" height="68" rx="8" fill="#26215C" stroke="#534AB7" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#CECBF6" text-anchor="middle" x="320" y="198">Execution Trace</text>
  <text font-size="11" fill="#7F77DD" text-anchor="middle" x="320" y="216">Live step stream</text>

  <rect x="412" y="172" width="188" height="68" rx="8" fill="#26215C" stroke="#534AB7" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#CECBF6" text-anchor="middle" x="506" y="198">Agent Simulation</text>
  <text font-size="11" fill="#7F77DD" text-anchor="middle" x="506" y="216">Demo mode (no backend)</text>

  <line x1="340" y1="256" x2="340" y2="300" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text font-size="11" fill="#64748b" x="352" y="282">REST + WebSocket</text>

  <!-- ── API ── -->
  <rect x="60" y="300" width="560" height="120" rx="14" fill="#0f2a25" stroke="#0F6E56" stroke-width="1"/>
  <text font-size="14" font-weight="600" fill="#5DCAA5" text-anchor="middle" x="340" y="326">FastAPI Backend — main.py</text>

  <rect x="80" y="336" width="148" height="68" rx="8" fill="#04342C" stroke="#0F6E56" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#9FE1CB" text-anchor="middle" x="154" y="362">REST Endpoints</text>
  <text font-size="11" fill="#1D9E75" text-anchor="middle" x="154" y="380">POST /run, GET /status</text>

  <rect x="246" y="336" width="148" height="68" rx="8" fill="#04342C" stroke="#0F6E56" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#9FE1CB" text-anchor="middle" x="320" y="362">WebSocket Stream</text>
  <text font-size="11" fill="#1D9E75" text-anchor="middle" x="320" y="380">ws://…/ws/agent</text>

  <rect x="412" y="336" width="188" height="68" rx="8" fill="#04342C" stroke="#0F6E56" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#9FE1CB" text-anchor="middle" x="506" y="362">Job Store</text>
  <text font-size="11" fill="#1D9E75" text-anchor="middle" x="506" y="380">In-memory / Redis</text>

  <line x1="340" y1="420" x2="340" y2="460" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ── AGENT CORE ── -->
  <rect x="60" y="460" width="560" height="120" rx="14" fill="#2a1f0a" stroke="#854F0B" stroke-width="1"/>
  <text font-size="14" font-weight="600" fill="#EF9F27" text-anchor="middle" x="340" y="486">NEXUS Agent Core — core.py</text>

  <rect x="80" y="496" width="148" height="68" rx="8" fill="#412402" stroke="#854F0B" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#FAC775" text-anchor="middle" x="154" y="522">ReAct Loop</text>
  <text font-size="11" fill="#BA7517" text-anchor="middle" x="154" y="540">Think → Act → Observe</text>

  <rect x="246" y="496" width="148" height="68" rx="8" fill="#412402" stroke="#854F0B" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#FAC775" text-anchor="middle" x="320" y="522">LLM Planner</text>
  <text font-size="11" fill="#BA7517" text-anchor="middle" x="320" y="540">Azure GPT-4o</text>

  <rect x="412" y="496" width="188" height="68" rx="8" fill="#412402" stroke="#854F0B" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#FAC775" text-anchor="middle" x="506" y="522">Error Recovery</text>
  <text font-size="11" fill="#BA7517" text-anchor="middle" x="506" y="540">Retry + replan logic</text>

  <line x1="200" y1="580" x2="200" y2="618" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="340" y1="580" x2="340" y2="618" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="480" y1="580" x2="480" y2="618" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ── TOOLS ── -->
  <rect x="60" y="618" width="560" height="120" rx="14" fill="#2a1510" stroke="#993C1D" stroke-width="1"/>
  <text font-size="14" font-weight="600" fill="#F0997B" text-anchor="middle" x="340" y="644">Tool Execution Layer</text>

  <rect x="80" y="654" width="118" height="68" rx="8" fill="#4A1B0C" stroke="#993C1D" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#F5C4B3" text-anchor="middle" x="139" y="678">Browser</text>
  <text font-size="11" fill="#D85A30" text-anchor="middle" x="139" y="698">Playwright</text>

  <rect x="210" y="654" width="118" height="68" rx="8" fill="#4A1B0C" stroke="#993C1D" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#F5C4B3" text-anchor="middle" x="269" y="678">Web Search</text>
  <text font-size="11" fill="#D85A30" text-anchor="middle" x="269" y="698">DuckDuckGo/Bing</text>

  <rect x="340" y="654" width="118" height="68" rx="8" fill="#4A1B0C" stroke="#993C1D" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#F5C4B3" text-anchor="middle" x="399" y="678">Extractor</text>
  <text font-size="11" fill="#D85A30" text-anchor="middle" x="399" y="698">LLM + BeautifulSoup</text>

  <rect x="470" y="654" width="130" height="68" rx="8" fill="#4A1B0C" stroke="#993C1D" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#F5C4B3" text-anchor="middle" x="535" y="678">Form Filler</text>
  <text font-size="11" fill="#D85A30" text-anchor="middle" x="535" y="698">Auto submit</text>

  <line x1="200" y1="738" x2="200" y2="778" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>
  <line x1="400" y1="738" x2="400" y2="778" stroke="#4a5568" stroke-width="1.5" marker-end="url(#arrow)"/>

  <!-- ── MEMORY ── -->
  <rect x="60" y="778" width="560" height="108" rx="14" fill="#0a1828" stroke="#185FA5" stroke-width="1"/>
  <text font-size="14" font-weight="600" fill="#85B7EB" text-anchor="middle" x="340" y="804">Memory Layer</text>

  <rect x="80" y="814" width="230" height="56" rx="8" fill="#042C53" stroke="#185FA5" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#B5D4F4" text-anchor="middle" x="195" y="836">Session Memory</text>
  <text font-size="11" fill="#378ADD" text-anchor="middle" x="195" y="856">Short-term context window</text>

  <rect x="370" y="814" width="230" height="56" rx="8" fill="#042C53" stroke="#185FA5" stroke-width="0.8"/>
  <text font-size="13" font-weight="500" fill="#B5D4F4" text-anchor="middle" x="485" y="836">Vector Memory</text>
  <text font-size="11" fill="#378ADD" text-anchor="middle" x="485" y="856">Pinecone — long-term recall</text>

  <!-- FEEDBACK ARROWS -->
  <path d="M640 832 L655 832 L655 520 L622 520" fill="none" stroke="#4a556866" stroke-width="1" stroke-dasharray="5 3" marker-end="url(#arrow)"/>
  <path d="M60 362 L40 362 L40 206 L60 206" fill="none" stroke="#4a556866" stroke-width="1" stroke-dasharray="5 3" marker-end="url(#arrow)"/>

  <!-- EXTERNAL SERVICES -->
  <rect x="78" y="882" width="120" height="28" rx="6" fill="#1e2535" stroke="#4a5568" stroke-width="0.6"/>
  <text font-size="11" fill="#94a3b8" text-anchor="middle" x="138" y="900">Azure OpenAI</text>

  <rect x="210" y="882" width="110" height="28" rx="6" fill="#1e2535" stroke="#4a5568" stroke-width="0.6"/>
  <text font-size="11" fill="#94a3b8" text-anchor="middle" x="265" y="900">Pinecone DB</text>

  <rect x="332" y="882" width="128" height="28" rx="6" fill="#1e2535" stroke="#4a5568" stroke-width="0.6"/>
  <text font-size="11" fill="#94a3b8" text-anchor="middle" x="396" y="900">Playwright/Chrome</text>

  <rect x="472" y="882" width="118" height="28" rx="6" fill="#1e2535" stroke="#4a5568" stroke-width="0.6"/>
  <text font-size="11" fill="#94a3b8" text-anchor="middle" x="531" y="900">DuckDuckGo</text>

</svg>

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

##  Hackathon Notes

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

MIT License — Built for Microsoft Hackathon 2025
Harshit !!!
