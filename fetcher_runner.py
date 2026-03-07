"""
Real-Time Market Sentiment — Fetcher Runner

Async orchestrator that runs all data fetchers on configurable timers.
Each fetcher runs in its own async loop and posts to the agent's /ingest endpoint.

Usage:
    python fetcher_runner.py                    # run all fetchers
    python fetcher_runner.py --no-reddit        # skip Reddit
    python fetcher_runner.py --no-rss           # skip RSS
    python fetcher_runner.py --no-sec           # skip SEC EDGAR
    python fetcher_runner.py --no-twitter       # skip Twitter mock
    python fetcher_runner.py --reddit-only      # only Reddit
    python fetcher_runner.py --agent-url http://localhost:9000
"""

import argparse
import asyncio
import logging
import signal
import sys

from fetchers.reddit import RedditFetcher
from fetchers.rss import RSSFetcher
from fetchers.sec_edgar import SECEdgarFetcher
from fetchers.twitter_mock import TwitterMockFetcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%H:%M]",
)
log = logging.getLogger("fetcher-runner")


async def main_async(args):
    agent_url = args.agent_url
    fetchers = []

    if args.reddit_only:
        fetchers.append(RedditFetcher(agent_url=agent_url))
    else:
        if not args.no_reddit:
            fetchers.append(RedditFetcher(agent_url=agent_url))
        if not args.no_rss:
            fetchers.append(RSSFetcher(agent_url=agent_url))
        if not args.no_sec:
            fetchers.append(SECEdgarFetcher(agent_url=agent_url))
        if not args.no_twitter:
            fetchers.append(TwitterMockFetcher(agent_url=agent_url))

    if not fetchers:
        log.error("No fetchers enabled. Use --help for options.")
        return

    log.info(f"Starting {len(fetchers)} fetcher(s):")
    for f in fetchers:
        log.info(f"   {f.source_type} (every {f.interval}s)")
    log.info(f"   Agent: {agent_url}")
    log.info("")

    tasks = [asyncio.create_task(f.run_loop()) for f in fetchers]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass


def main():
    parser = argparse.ArgumentParser(description="Market Sentiment Fetcher Runner")
    parser.add_argument("--agent-url", default="http://localhost:8888", help="Agent API URL (default: http://localhost:8888)")
    parser.add_argument("--no-reddit", action="store_true", help="Disable Reddit fetcher")
    parser.add_argument("--no-rss", action="store_true", help="Disable RSS fetcher")
    parser.add_argument("--no-sec", action="store_true", help="Disable SEC EDGAR fetcher")
    parser.add_argument("--no-twitter", action="store_true", help="Disable Twitter mock fetcher")
    parser.add_argument("--reddit-only", action="store_true", help="Only run Reddit fetcher")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()

    def shutdown(sig):
        log.info(f"\nShutting down fetchers (signal {sig})...")
        for task in asyncio.all_tasks(loop):
            task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown, sig)

    try:
        loop.run_until_complete(main_async(args))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        loop.close()
        log.info("Fetchers stopped.")


if __name__ == "__main__":
    main()
