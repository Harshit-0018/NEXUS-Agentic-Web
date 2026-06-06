"""
Session Memory
==============
Short-term memory for the agent's current execution context.
Stores recent actions and observations in a sliding window.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any, Optional
import time


@dataclass
class MemoryEntry:
    action: str
    inputs: dict
    observation: str
    timestamp: float


class SessionMemory:
    """
    Maintains a sliding window of recent agent actions.
    Used to prevent loops and provide context to the LLM.
    """

    def __init__(self, max_entries: int = 20):
        self._entries: deque[MemoryEntry] = deque(maxlen=max_entries)

    def add(self, action: str, inputs: dict, observation: str):
        """Add a new memory entry."""
        self._entries.append(MemoryEntry(
            action=action,
            inputs=inputs,
            observation=observation[:500],  # Cap observation size
            timestamp=time.time(),
        ))

    def get_recent(self, n: int = 5) -> list[MemoryEntry]:
        """Get the n most recent entries."""
        entries = list(self._entries)
        return entries[-n:] if len(entries) >= n else entries

    def has_visited(self, url: str) -> bool:
        """Check if a URL was recently visited."""
        for entry in self._entries:
            if entry.action == "browser_navigate" and entry.inputs.get("url") == url:
                return True
        return False

    def to_context_string(self) -> str:
        """Format recent memory as LLM-readable context."""
        if not self._entries:
            return "No prior actions."
        lines = []
        for entry in list(self._entries)[-8:]:
            lines.append(f"- {entry.action}({entry.inputs}) → {entry.observation[:80]}...")
        return "\n".join(lines)

    def clear(self):
        """Clear all memory."""
        self._entries.clear()
