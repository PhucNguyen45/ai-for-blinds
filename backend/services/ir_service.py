"""
IR service — Information Retrieval over the Internet.

Two retrieval channels aligned with the SgBE proposal
("Google Search + configured news sites + TF-IDF"):

1. **Web** — DuckDuckGo search (no API key required).
2. **News** — Vietnamese RSS feeds (vnexpress, dantri...) fetched and
   cached on disk, ranked against the user's query with TF-IDF.

Results from both channels are merged and returned with source + score.
"""

import json
import logging
import math
import os
import re
import time
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

from backend.config import settings

# Name of the DuckDuckGo result feed keys (stable across duckduckgo_search
# versions 6.x–8.x).
_DDG_KEYS = ("title", "href", "body")


def _tokenize(text: str) -> list[str]:
    """Tokenize Vietnamese/English text into lowercase word tokens."""
    return re.findall(r"\w+", text.lower())


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


class _TfIdfIndex:
    """Minimal pure-Python TF-IDF index (no scikit-learn dependency)."""

    def __init__(self, documents: list[str]) -> None:
        self._corpus: list[list[str]] = [_tokenize(d) for d in documents]
        n = len(self._corpus)
        df: Counter = Counter()
        for tokens in self._corpus:
            df.update(set(tokens))
        self._idf = {term: math.log((n + 1) / (count + 1)) + 1 for term, count in df.items()}

    def score(self, query: str) -> list[float]:
        """Return a 0..1 normalized TF-IDF score per document."""
        query_tokens = Counter(_tokenize(query))
        raw: list[float] = []
        for tokens in self._corpus:
            tf = Counter(tokens)
            total = len(tokens) or 1
            score = 0.0
            for term, count in query_tokens.items():
                if term in self._idf:
                    score += (tf[term] / total) * self._idf[term] * count
            raw.append(score)
        max_score = max(raw) if raw else 0.0
        if max_score <= 0:
            return [0.0] * len(raw)
        return [s / max_score for s in raw]


class IrService:
    """Internet retrieval service (lazy singleton)."""

    # ── Availability ─────────────────────────────────────────
    @property
    def available(self) -> bool:
        return True  # network-backed; availability checked per request

    # ── News (RSS + TF-IDF) ──────────────────────────────────
    def _load_news(self) -> list[dict[str, str]]:
        """Fetch RSS news entries, caching to disk with a TTL."""
        cache_file = os.path.join(settings.news_cache_dir, "news_cache.json")
        os.makedirs(settings.news_cache_dir, exist_ok=True)

        if os.path.exists(cache_file):
            age_hours = (time.time() - os.path.getmtime(cache_file)) / 3600
            if age_hours < settings.news_refresh_hours:
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    if isinstance(cached, list):
                        return cached
                except Exception as e:
                    logger.warning(f"Failed to read news cache: {e}")

        entries: list[dict[str, str]] = []
        try:
            import feedparser

            for feed_url in settings.news_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries[:20]:
                        entries.append(
                            {
                                "title": (getattr(entry, "title", "") or "").strip(),
                                "summary": _strip_html(getattr(entry, "summary", "") or ""),
                                "link": (getattr(entry, "link", "") or "").strip(),
                                "source": feed_url,
                                "published": (getattr(entry, "published", "") or "").strip(),
                            }
                        )
                except Exception as e:
                    logger.warning(f"RSS fetch failed for {feed_url}: {e}")
        except Exception as e:
            logger.warning(f"feedparser unavailable: {e}")

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to write news cache: {e}")

        return entries

    def _search_news(self, query: str, n: int) -> list[dict[str, Any]]:
        entries = self._load_news()
        if not entries:
            return []

        corpus = [f"{e['title']} {e['summary']}".strip() for e in entries]
        index = _TfIdfIndex(corpus)
        scores = index.score(query)

        ranked: list[tuple[float, dict[str, str]]] = []
        for entry, score in zip(entries, scores):
            if score <= 0:
                continue
            ranked.append((score, entry))
        ranked.sort(key=lambda item: item[0], reverse=True)

        results = []
        for score, entry in ranked[:n]:
            results.append(
                {
                    "title": entry["title"],
                    "snippet": entry["summary"],
                    "url": entry["link"],
                    "source": "news",
                    "score": round(score, 3),
                }
            )
        return results

    # ── Web (DuckDuckGo) ─────────────────────────────────────
    def _search_web(self, query: str, n: int) -> list[dict[str, Any]]:
        try:
            from ddgs import DDGS
        except Exception as e:
            logger.warning(f"ddgs unavailable: {e}")
            return []

        for attempt in range(2):
            try:
                with DDGS() as ddgs:
                    raw_results = list(ddgs.text(query, region="vn-vn", max_results=n))
                if raw_results:
                    break
                logger.warning(f"DuckDuckGo empty result set (attempt {attempt + 1})")
            except Exception as e:
                logger.warning(f"DuckDuckGo search error (attempt {attempt + 1}): {e}")
                raw_results = []
        else:
            raw_results = []

        results = []
        total = len(raw_results)
        for i, item in enumerate(raw_results):
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            url = str(item.get("href") or item.get("url") or "")
            body = str(item.get("body") or "")
            results.append(
                {
                    "title": _strip_html(title),
                    "snippet": _strip_html(body),
                    "url": url,
                    "source": "web",
                    "score": round((total - i) / max(total, 1), 3),
                }
            )
        return results

    # ── Public API ───────────────────────────────────────────
    def search(self, query: str, n_results: int = 5) -> list[dict[str, Any]]:
        """Search web + Vietnamese news, merging results by relevance."""
        query = (query or "").strip()
        if not query:
            return []

        news_results = self._search_news(query, n_results)
        web_results = self._search_web(query, n_results)

        merged = news_results + web_results
        merged.sort(key=lambda r: r.get("score", 0.0), reverse=True)
        return merged[:n_results]


# Singleton instance
ir_service = IrService()
