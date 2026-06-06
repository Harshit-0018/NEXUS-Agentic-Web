"""
NEXUS Agent Core
================
The main autonomous agent engine. Implements a ReAct-style
(Reasoning + Acting) loop with:
  - LLM-powered planning and decision-making
  - Tool use (browser, search, extract, interact)
  - Short-term memory (context window)
  - Long-term memory (Pinecone vector store)
  - Error recovery and replanning
  - Real-time execution trace via WebSocket
"""

import asyncio
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import AsyncGenerator, Optional
from datetime import datetime

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.tools import BaseTool

from .tools.browser import BrowserTool
from .tools.search import WebSearchTool
from .tools.extractor import DataExtractorTool
from .tools.form_filler import FormFillerTool
from .memory.session_memory import SessionMemory
from .memory.vector_store import VectorMemory
from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


# ─── Data Models ────────────────────────────────────────────────────────────

class StepType(str, Enum):
    THINK   = "think"
    BROWSE  = "browse"
    EXTRACT = "extract"
    ACTION  = "action"
    ERROR   = "error"
    DONE    = "done"


@dataclass
class AgentStep:
    """Single step in the agent execution trace."""
    step_num:    int
    step_type:   StepType
    label:       str
    text:        str
    icon:        str
    timestamp:   float = field(default_factory=time.time)
    elapsed_ms:  int = 0
    url:         Optional[str] = None
    data:        Optional[dict] = None
    confidence:  Optional[float] = None

    def to_dict(self):
        d = asdict(self)
        d["step_type"] = self.step_type.value
        return d


@dataclass
class AgentResult:
    """Final result after agent task completion."""
    success:     bool
    task:        str
    output:      dict
    raw_text:    str
    steps_used:  int
    elapsed_s:   float
    trace:       list[AgentStep]
    error:       Optional[str] = None


# ─── System Prompt ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are NEXUS, an autonomous web agent. Your role is to complete tasks on the web on behalf of users.

You operate in a structured loop:
1. THINK: Analyze the task, plan the approach step-by-step
2. ACT: Use one of your available tools
3. OBSERVE: Process the tool result
4. EVALUATE: Decide next action or if task is complete

RULES:
- Be methodical. Break complex tasks into smaller subtasks.
- Always verify data from multiple sources when accuracy matters.
- If a step fails, retry with an alternate strategy before giving up.
- Report confidence scores with extracted data (0.0–1.0).
- When done, return structured JSON with all extracted/computed information.
- Be concise in your reasoning. Act efficiently.

AVAILABLE TOOLS:
- browser_navigate: Navigate to a URL
- web_search: Search the web for information
- extract_data: Extract structured data from current page
- fill_form: Fill and submit a web form
- scroll_page: Scroll the current page
- click_element: Click an element by selector or description
- take_screenshot: Capture current browser state

OUTPUT FORMAT for each action:
{
  "thought": "What I'm thinking",
  "action": "tool_name",
  "action_input": { ... },
  "confidence": 0.85
}

When task is complete, output:
{
  "thought": "Task complete because...",
  "action": "FINISH",
  "final_answer": { ... }
}
"""


# ─── NEXUS Agent ─────────────────────────────────────────────────────────────

class NexusAgent:
    """
    The core autonomous agent. Runs a ReAct loop until task is complete
    or max_steps is reached. Streams steps via async generator.
    """

    def __init__(self):
        self.llm = self._init_llm()
        self.browser = BrowserTool()
        self.searcher = WebSearchTool()
        self.extractor = DataExtractorTool()
        self.form_filler = FormFillerTool()
        self.tools = {
            "browser_navigate": self.browser.navigate,
            "web_search":       self.searcher.search,
            "extract_data":     self.extractor.extract,
            "fill_form":        self.form_filler.fill,
        }
        self.session_memory = SessionMemory()
        self.vector_memory = VectorMemory()

    def _init_llm(self):
        """Initialize LLM from Azure OpenAI or fallback to OpenAI."""
        try:
            return AzureChatOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
                api_key=settings.AZURE_OPENAI_KEY,
                api_version=settings.AZURE_OPENAI_VERSION,
                temperature=0.2,
                max_tokens=2000,
                streaming=False,
            )
        except Exception:
            logger.warning("Azure OpenAI not configured, falling back to OpenAI")
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.OPENAI_API_KEY,
                temperature=0.2,
            )

    async def run(
        self,
        task: str,
        mode: str = "autonomous",
        max_steps: int = 20,
    ) -> AsyncGenerator[AgentStep, None]:
        """
        Run the agent on a task. Yields AgentStep objects as execution proceeds.
        This is the main entry point for streaming execution.
        """
        start_time = time.time()
        conversation_history = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Complete this task: {task}")
        ]

        # Check long-term memory for similar tasks
        prior_knowledge = await self.vector_memory.search(task)
        if prior_knowledge:
            conversation_history.append(
                HumanMessage(content=f"Relevant prior knowledge: {prior_knowledge}")
            )

        step_num = 0
        last_url = None

        # Initial planning step
        step_num += 1
        yield AgentStep(
            step_num=step_num,
            step_type=StepType.THINK,
            label="PLANNING",
            icon="🧠",
            text=f"Analyzing task: '{task[:80]}{'...' if len(task) > 80 else ''}'. Decomposing into subtasks.",
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

        for iteration in range(max_steps):
            step_num += 1
            elapsed_ms = int((time.time() - start_time) * 1000)

            try:
                # Ask LLM what to do next
                response = await self._call_llm(conversation_history)
                parsed = self._parse_response(response)

                if not parsed:
                    # LLM gave unparseable output — retry once
                    conversation_history.append(AIMessage(content=response))
                    conversation_history.append(HumanMessage(
                        content="Your last response was not valid JSON. Please respond with valid JSON only."
                    ))
                    continue

                thought = parsed.get("thought", "")
                action = parsed.get("action", "")
                action_input = parsed.get("action_input", {})
                confidence = parsed.get("confidence", None)

                # ── FINISH ──────────────────────────────────────────────────
                if action == "FINISH":
                    final_answer = parsed.get("final_answer", {})
                    yield AgentStep(
                        step_num=step_num,
                        step_type=StepType.DONE,
                        label="COMPLETE",
                        icon="✅",
                        text=f"Task completed. {thought}",
                        elapsed_ms=elapsed_ms,
                        data=final_answer,
                        confidence=confidence,
                    )
                    # Store in long-term memory
                    await self.vector_memory.store(task, str(final_answer))
                    return

                # ── TOOL EXECUTION ──────────────────────────────────────────
                tool_fn = self.tools.get(action)
                if not tool_fn:
                    yield AgentStep(
                        step_num=step_num,
                        step_type=StepType.ERROR,
                        label="UNKNOWN TOOL",
                        icon="⚠️",
                        text=f"Unknown tool: '{action}'. Replanning...",
                        elapsed_ms=elapsed_ms,
                    )
                    conversation_history.append(AIMessage(content=response))
                    conversation_history.append(HumanMessage(
                        content=f"Tool '{action}' does not exist. Available: {list(self.tools.keys())}"
                    ))
                    continue

                # Emit step for the action
                step_type, icon, label = self._categorize_action(action)
                step_text = self._describe_action(action, action_input, thought)
                step_url = action_input.get("url") if action == "browser_navigate" else None

                yield AgentStep(
                    step_num=step_num,
                    step_type=step_type,
                    label=label,
                    icon=icon,
                    text=step_text,
                    elapsed_ms=elapsed_ms,
                    url=step_url,
                    confidence=confidence,
                )

                # Execute the tool
                try:
                    tool_result = await tool_fn(**action_input)
                    if isinstance(tool_result, dict) and tool_result.get("url"):
                        last_url = tool_result["url"]
                    observation = json.dumps(tool_result) if isinstance(tool_result, dict) else str(tool_result)
                except Exception as tool_err:
                    observation = f"Tool error: {str(tool_err)}"
                    step_num += 1
                    yield AgentStep(
                        step_num=step_num,
                        step_type=StepType.ERROR,
                        label="TOOL ERROR",
                        icon="⚡",
                        text=f"Error in {action}: {str(tool_err)[:100]}. Attempting recovery...",
                        elapsed_ms=int((time.time() - start_time) * 1000),
                    )

                # Feed result back to LLM
                conversation_history.append(AIMessage(content=response))
                conversation_history.append(HumanMessage(
                    content=f"Observation from {action}: {observation[:2000]}"
                ))

                # Update session memory
                self.session_memory.add(action, action_input, observation[:500])

            except asyncio.CancelledError:
                yield AgentStep(
                    step_num=step_num,
                    step_type=StepType.ERROR,
                    label="CANCELLED",
                    icon="⛔",
                    text="Agent execution cancelled.",
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                return

            except Exception as e:
                logger.error(f"Agent loop error at step {step_num}: {e}")
                yield AgentStep(
                    step_num=step_num,
                    step_type=StepType.ERROR,
                    label="ERROR",
                    icon="❌",
                    text=f"Unexpected error: {str(e)[:120]}. Attempting replan...",
                    elapsed_ms=int((time.time() - start_time) * 1000),
                )
                await asyncio.sleep(1)

        # Max steps reached
        yield AgentStep(
            step_num=step_num + 1,
            step_type=StepType.ERROR,
            label="MAX STEPS",
            icon="⚠️",
            text=f"Reached maximum step limit ({max_steps}). Returning partial results.",
            elapsed_ms=int((time.time() - start_time) * 1000),
        )

    async def _call_llm(self, messages: list) -> str:
        """Invoke the LLM and return string response."""
        response = await self.llm.ainvoke(messages)
        return response.content

    def _parse_response(self, response: str) -> Optional[dict]:
        """Parse JSON from LLM response, with fence stripping."""
        try:
            # Strip markdown fences
            clean = response.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            return json.loads(clean.strip())
        except (json.JSONDecodeError, IndexError):
            # Try extracting JSON block from within text
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return None

    def _categorize_action(self, action: str) -> tuple[StepType, str, str]:
        """Map tool name to step type, icon, label."""
        mapping = {
            "browser_navigate": (StepType.BROWSE,   "🌐", "NAVIGATE"),
            "web_search":       (StepType.BROWSE,   "🔍", "SEARCH"),
            "extract_data":     (StepType.EXTRACT,  "📋", "EXTRACT"),
            "fill_form":        (StepType.ACTION,   "✍️", "FORM FILL"),
            "click_element":    (StepType.ACTION,   "👆", "CLICK"),
            "scroll_page":      (StepType.ACTION,   "📜", "SCROLL"),
            "take_screenshot":  (StepType.BROWSE,   "📸", "SCREENSHOT"),
        }
        return mapping.get(action, (StepType.ACTION, "⚡", action.upper()))

    def _describe_action(self, action: str, inputs: dict, thought: str) -> str:
        """Generate human-readable description of an action."""
        if action == "browser_navigate":
            return f"Navigating to <strong>{inputs.get('url', 'URL')}</strong>"
        if action == "web_search":
            return f"Searching: <strong>\"{inputs.get('query', '')}\"</strong>"
        if action == "extract_data":
            return f"Extracting data: {inputs.get('schema', 'structured information')}"
        if action == "fill_form":
            return f"Filling form with {len(inputs.get('fields', {}))} fields"
        return thought[:120] if thought else f"Executing: {action}"

    async def cleanup(self):
        """Clean up browser and connections."""
        await self.browser.close()
