"""
RSS fetcher — parses Yahoo Finance and MarketWatch RSS feeds.

Uses xml.etree.ElementTree (stdlib only, no feedparser dependency).
Handles both RSS 2.0 and Atom feed formats.
"""

import logging
import re
import xml.etree.ElementTree as ET

import requests

from config import RSS_FEEDS, RSS_INTERVAL
from fetchers.base import BaseFetcher

log = logging.getLogger("fetcher.rss")

# Atom namespace
ATOM_NS = "http://www.w3.org/2005/Atom"


def strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    return re.sub(r"<[^>]+>", "", text).strip()


class RSSFetcher(BaseFetcher):
    source_type = "rss"

    def __init__(self, agent_url: str = "http://localhost:8888", interval: int = RSS_INTERVAL,
                 feed_urls: list[str] | None = None):
        super().__init__(agent_url=agent_url, interval=interval)
        self.feed_urls = feed_urls or RSS_FEEDS
        self.headers = {
            "User-Agent": "MarketSentimentBot/1.0 (research)",
        }

    def _parse_rss(self, xml_text: str, feed_url: str) -> list[dict]:
        """Parse RSS 2.0 format."""
        items = []
        try:
            root = ET.fromstring(xml_text)

            # RSS 2.0: root/channel/item
            for item in root.findall(".//item"):
                title = item.findtext("title", "").strip()
                description = strip_html(item.findtext("description", ""))
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()

                if not title:
                    continue

                text = title
                if description:
                    text += f"\n\n{description[:1500]}"

                source_parts = [feed_url.split("/")[2]]  # domain
                if pub_date:
                    source_parts.append(pub_date)

                items.append({
                    "text": text,
                    "source": " | ".join(source_parts),
                    "url": link,
                })
        except ET.ParseError:
            pass
        return items

    def _parse_atom(self, xml_text: str, feed_url: str) -> list[dict]:
        """Parse Atom format."""
        items = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": ATOM_NS}

            for entry in root.findall("atom:entry", ns):
                title = entry.findtext("atom:title", "", ns).strip()
                summary = strip_html(entry.findtext("atom:summary", "", ns))
                content = strip_html(entry.findtext("atom:content", "", ns))
                link_el = entry.find("atom:link", ns)
                link = link_el.get("href", "") if link_el is not None else ""
                updated = entry.findtext("atom:updated", "", ns).strip()

                if not title:
                    continue

                body = content or summary
                text = title
                if body:
                    text += f"\n\n{body[:1500]}"

                source_parts = [feed_url.split("/")[2]]
                if updated:
                    source_parts.append(updated[:19])

                items.append({
                    "text": text,
                    "source": " | ".join(source_parts),
                    "url": link,
                })
        except ET.ParseError:
            pass
        return items

    def fetch(self) -> list[dict]:
        all_items = []
        for feed_url in self.feed_urls:
            try:
                resp = requests.get(feed_url, headers=self.headers, timeout=15)
                if resp.status_code != 200:
                    log.warning(f"RSS {feed_url} returned {resp.status_code}")
                    continue

                xml_text = resp.text

                # Try RSS 2.0 first, then Atom
                items = self._parse_rss(xml_text, feed_url)
                if not items:
                    items = self._parse_atom(xml_text, feed_url)

                all_items.extend(items)
                log.debug(f"RSS {feed_url}: {len(items)} items")

            except Exception as e:
                log.error(f"RSS {feed_url} fetch error: {e}")

        return all_items
