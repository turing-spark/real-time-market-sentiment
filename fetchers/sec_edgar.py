"""
SEC EDGAR fetcher — queries the free public EDGAR full-text search API
for recent Form 4 (insider trading) and 13F-HR (institutional holdings) filings.

Uses the EDGAR full-text search API: https://efts.sec.gov/LATEST/search-index
"""

import logging
from datetime import datetime, timedelta, timezone

import requests

from config import SEC_INTERVAL, SEC_USER_AGENT, SEC_FILING_TYPES
from fetchers.base import BaseFetcher

log = logging.getLogger("fetcher.sec")


class SECEdgarFetcher(BaseFetcher):
    source_type = "sec_edgar"

    def __init__(self, agent_url: str = "http://localhost:8888", interval: int = SEC_INTERVAL):
        super().__init__(agent_url=agent_url, interval=interval)
        self.headers = {
            "User-Agent": SEC_USER_AGENT,
            "Accept": "application/json",
        }

    def fetch(self) -> list[dict]:
        items = []
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = now.strftime("%Y-%m-%d")

        for form_type in SEC_FILING_TYPES:
            try:
                # EDGAR full-text search API
                url = "https://efts.sec.gov/LATEST/search-index"
                params = {
                    "q": f'"{form_type}"',
                    "dateRange": "custom",
                    "startdt": start_date,
                    "enddt": end_date,
                    "forms": form_type,
                }

                resp = requests.get(url, params=params, headers=self.headers, timeout=15)

                if resp.status_code == 429:
                    log.warning("SEC EDGAR rate limited, backing off")
                    continue
                if resp.status_code != 200:
                    # Fallback: try the simpler recent filings endpoint
                    items.extend(self._fetch_recent_filings(form_type, start_date, end_date))
                    continue

                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])

                for hit in hits[:15]:  # Limit per form type
                    source_data = hit.get("_source", {})
                    entity_name = source_data.get("entity_name", "Unknown")
                    file_date = source_data.get("file_date", "")
                    display_names = source_data.get("display_names", [])
                    file_num = source_data.get("file_num", "")

                    # Build descriptive text
                    if form_type == "4":
                        text = f"SEC Form 4 (Insider Transaction): {entity_name} filed on {file_date}."
                        if display_names:
                            text += f" Reported by: {', '.join(display_names[:3])}."
                    else:
                        text = f"SEC Form 13F-HR (Institutional Holdings): {entity_name} filed on {file_date}."

                    items.append({
                        "text": text,
                        "source": f"SEC EDGAR | {form_type} | {entity_name}",
                    })

            except Exception as e:
                log.error(f"SEC EDGAR {form_type} fetch error: {e}")

        return items

    def _fetch_recent_filings(self, form_type: str, start_date: str, end_date: str) -> list[dict]:
        """Fallback: query EDGAR recent filings RSS feed."""
        items = []
        try:
            # Use EDGAR company search as fallback
            url = f"https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                "action": "getcurrent",
                "type": form_type,
                "dateb": "",
                "owner": "include",
                "count": "10",
                "search_text": "",
                "output": "atom",
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=15)
            if resp.status_code == 200:
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom"}
                    for entry in root.findall("atom:entry", ns)[:10]:
                        title = entry.findtext("atom:title", "", ns).strip()
                        summary = entry.findtext("atom:summary", "", ns).strip()
                        if title:
                            text = f"SEC Filing: {title}"
                            if summary:
                                text += f"\n{summary[:500]}"
                            items.append({
                                "text": text,
                                "source": f"SEC EDGAR | {form_type}",
                            })
                except ET.ParseError:
                    pass
        except Exception as e:
            log.error(f"SEC EDGAR fallback error: {e}")
        return items
