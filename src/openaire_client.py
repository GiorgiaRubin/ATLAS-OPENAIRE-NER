# Client for querying the OpenAIRE Graph API and counting keyword occurrences.
# Includes caching, keyword sanitization, and error handling to stabilize the pipeline.

import requests
import time
import json
import re
import hashlib
from pathlib import Path


class OpenAIREClient:

    def __init__(
        self,
        base_url: str,
        page_size: int = 100,
        max_pages: int = 50,
        sleep_seconds: float = 0.2,
        cache_dir: str = "data/cache",
        token: str = ""
    ):
        #Initialize the client and configure API parameters + caching
        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self.max_pages = max_pages
        self.sleep_seconds = sleep_seconds
        self.token = token

        # in-memory cache
        self._cache_counts = {}

        # filesystem cache
        self.cache_dir = Path(cache_dir) / "openaire"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    #--- Clean and normalize a keyword to avoid API errors ---
    def _clean_keyword(self, kw: str) -> str:
        kw = kw.strip()
        kw = re.sub(r"\(.*?\)", "", kw)
        kw = re.sub(r"[^a-zA-Z0-9\s]", "", kw)
        kw = " ".join(kw.split())
        return kw
    
    #--- Generate a deterministic cache file path based on a keyword hash ---
    def _cache_path(self, keyword: str) -> Path:
        h = hashlib.md5(keyword.encode()).hexdigest()
        return self.cache_dir / f"{h}.json"

    #--- Load cached results from disk if present and valid ---
    def _load_cache(self, keyword: str):
        p = self._cache_path(keyword)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except:
                return None
        return None
    
    #--- Save API results to disk cache ---
    def _save_cache(self, keyword: str, data: dict):
        p = self._cache_path(keyword)
        try:
            p.write_text(json.dumps(data))
        except:
            pass

    #--- Perform a GET request with lightweight retry logic ---
    def _get(self, params: dict):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        for attempt in range(3):
            try:
                r = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=30
                )

                print(r.url)

                if r.status_code == 400:
                    raise Exception("Bad query")

                r.raise_for_status()
                return r.json()

            except Exception as e:
                if attempt == 2:
                    raise e
                time.sleep(1)

        return {}

    #--- Count keyword occurrences in a specific OpenAIRE field ---
    def _count(self, field: str, keyword: str) -> int:
        kw = self._clean_keyword(keyword)

        if not kw or kw.strip() == "":
            print(f"[DEBUG] Discarded empty keyword: '{keyword}'")
            return 0

        params = {
            field: kw,
            "page": 1,
            "pageSize": 10
        }

        try:
            data = self._get(params)
            return data.get("header", {}).get("numFound", 0)

        except Exception as e:
            print(f"[WARNING] OpenAIRE error for '{kw}': {e}")
            return 0

    #--- Count occurrences of a keyword across main OpenAIRE fields (with caching) ---
    def count_all_fields(self, keyword: str) -> dict:
        kw = self._clean_keyword(keyword)

        if not kw:
            return {
                "count_title": 0,
                "count_desc": 0
            }

        # RAM cache
        if kw in self._cache_counts:
            return self._cache_counts[kw]

        # file cache
        cached = self._load_cache(kw)
        if cached:
            self._cache_counts[kw] = cached
            return cached

        # API queries
        result = {
            "keyword": kw,
            "count_title": self._count("mainTitle", kw),
            "count_desc": self._count("description", kw),
            "count_subject": self._count("subjects", kw)
        }

        # save to both caches
        self._cache_counts[kw] = result
        self._save_cache(kw, result)

        time.sleep(self.sleep_seconds)

        return result
