"""
Base fetcher with dedup and post-to-agent functionality.
"""

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod

import requests

log = logging.getLogger("fetcher")


class BaseFetcher(ABC):
    """Abstract base class for all data fetchers.

    Provides:
    - In-memory dedup via content hashing
    - post_to_agent() to send items to the agent's /ingest endpoint
    - run_once() to fetch + dedup + post
    - run_loop() for continuous fetching on an interval
    """

    source_type: str = ""  # Override in subclasses

    def __init__(self, agent_url: str = "http://localhost:8888", interval: int = 120):
        self.agent_url = agent_url
        self.interval = interval
        self._seen: set[str] = set()

    @abstractmethod
    def fetch(self) -> list[dict]:
        """Fetch new items from the data source.

        Returns:
            List of dicts with at minimum 'text' and 'source' keys.
        """
        ...

    def _content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]

    def post_to_agent(self, item: dict) -> bool:
        """Post a single item to the agent's /ingest endpoint.

        Args:
            item: dict with 'text', 'source', and optionally other fields.

        Returns:
            True if successfully posted, False otherwise.
        """
        try:
            resp = requests.post(
                f"{self.agent_url}/ingest",
                json={
                    "text": item["text"],
                    "source": item.get("source", self.source_type),
                    "source_type": self.source_type,
                },
                timeout=30,
            )
            return resp.status_code == 200
        except Exception as e:
            log.error(f"[{self.source_type}] Failed to post to agent: {e}")
            return False

    def run_once(self) -> int:
        """Fetch, dedup, and post new items. Returns count of new items posted."""
        try:
            items = self.fetch()
        except Exception as e:
            log.error(f"[{self.source_type}] Fetch error: {e}")
            return 0

        posted = 0
        for item in items:
            content_hash = self._content_hash(item["text"])
            if content_hash in self._seen:
                continue
            self._seen.add(content_hash)

            if self.post_to_agent(item):
                posted += 1
                log.info(f"[{self.source_type}] Posted: {item.get('source', '')[:60]}")

        if posted:
            log.info(f"[{self.source_type}] Fetched {len(items)} items, posted {posted} new")
        return posted

    async def run_loop(self):
        """Run fetch loop continuously at the configured interval."""
        log.info(f"[{self.source_type}] Starting fetch loop (every {self.interval}s)")
        while True:
            self.run_once()
            await asyncio.sleep(self.interval)
