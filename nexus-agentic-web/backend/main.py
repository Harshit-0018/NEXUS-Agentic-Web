"""
NEXUS — FastAPI Backend
=======================
REST + WebSocket API for the NEXUS autonomous agent platform.

Endpoints:
  POST /api/run        — Start a task (returns job_id)
  GET  /api/status     — Check task status
  WS   /ws/agent       — Stream agent execution in real-time
  GET  /api/health     — Health check
"""

import asyncio
import json
import uuid
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from agent.core import NexusAgent, AgentStep, StepType
from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# ─── In-memory job store (use Redis in production) ───────────────────────────
jobs: dict[str, dict] = {}
active_connections: dict[str, WebSocket] = {}


# ─── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 NEXUS Agent API starting up...")
    yield
    logger.info("🛑 NEXUS Agent API shutting down...")


# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NEXUS Agentic Web API",
    description="Autonomous AI agent that browses, extracts, and acts on the web",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request / Response Models ────────────────────────────────────────────────
class RunTaskRequest(BaseModel):
    task: str = Field(..., min_length=5, max_length=1000, description="Natural language task description")
    mode: str = Field("autonomous", pattern="^(autonomous|supervised|readonly)$")
    max_steps: int = Field(20, ge=1, le=50)
    output_format: str = Field("json", pattern="^(json|text|markdown)$")


class RunTaskResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ─── REST Endpoints ───────────────────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "nexus-agent", "version": "1.0.0"}


@app.post("/api/run", response_model=RunTaskResponse)
async def run_task(request: RunTaskRequest, background_tasks: BackgroundTasks):
    """Start an agent task. Returns job_id for polling or WebSocket connection."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "queued",
        "task": request.task,
        "steps": [],
        "result": None,
        "error": None,
    }

    background_tasks.add_task(
        execute_agent_task,
        job_id=job_id,
        task=request.task,
        mode=request.mode,
        max_steps=request.max_steps,
    )

    logger.info(f"Job {job_id} queued: {request.task[:60]}...")
    return RunTaskResponse(
        job_id=job_id,
        status="queued",
        message="Agent task started. Connect to /ws/agent/{job_id} for real-time stream.",
    )


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    """Poll for job status and results."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.delete("/api/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running agent task."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job["status"] = "cancelled"
    return {"message": "Cancellation requested"}


# ─── WebSocket ────────────────────────────────────────────────────────────────
@app.websocket("/ws/agent")
async def websocket_agent(
    websocket: WebSocket,
    task: str,
    mode: str = "autonomous",
    max_steps: int = 20,
):
    """
    Real-time streaming WebSocket endpoint.
    Sends each agent step as a JSON message as it happens.

    Connect with: ws://localhost:8000/ws/agent?task=YOUR_TASK&max_steps=20
    """
    await websocket.accept()
    conn_id = str(uuid.uuid4())
    active_connections[conn_id] = websocket

    logger.info(f"WebSocket {conn_id} connected. Task: {task[:60]}...")

    # Send connection confirmation
    await websocket.send_json({
        "type": "connected",
        "conn_id": conn_id,
        "message": "Agent session started",
    })

    agent = NexusAgent()

    try:
        async for step in agent.run(task=task, mode=mode, max_steps=max_steps):
            # Check if client is still there
            try:
                await websocket.send_json({
                    "type": "step",
                    "data": step.to_dict(),
                })
            except WebSocketDisconnect:
                logger.info(f"Client {conn_id} disconnected mid-stream")
                break

            # Small yield to allow cancellation processing
            await asyncio.sleep(0)

        await websocket.send_json({"type": "done", "message": "Agent execution complete"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket {conn_id} disconnected")

    except Exception as e:
        logger.error(f"WebSocket error for {conn_id}: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass

    finally:
        active_connections.pop(conn_id, None)
        await agent.cleanup()


# ─── Background Task ──────────────────────────────────────────────────────────
async def execute_agent_task(job_id: str, task: str, mode: str, max_steps: int):
    """Run agent in background and update job store."""
    job = jobs.get(job_id)
    if not job:
        return

    job["status"] = "running"
    agent = NexusAgent()

    try:
        async for step in agent.run(task=task, mode=mode, max_steps=max_steps):
            job["steps"].append(step.to_dict())

            if step.step_type == StepType.DONE:
                job["status"] = "complete"
                job["result"] = step.data
            elif step.step_type == StepType.ERROR and "MAX STEPS" in step.label:
                job["status"] = "partial"

            # Check for external cancellation
            if job.get("status") == "cancelled":
                break

    except Exception as e:
        logger.error(f"Background task error for {job_id}: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
    finally:
        if job["status"] == "running":
            job["status"] = "complete"
        await agent.cleanup()
