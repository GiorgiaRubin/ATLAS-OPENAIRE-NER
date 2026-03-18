# Client per interrogare OpenAIRE Graph API e contare occorrenze di keyword
# Include caching, sanitizzazione keyword e gestione errori per stabilizzare la pipeline

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
        """
        base_url: endpoint OpenAIRE
        page_size: dimensione pagina API
        max_pages: limite sicurezza
        sleep_seconds: pausa tra richieste
        cache_dir: directory cache
        token: eventuale token API
        """

        self.base_url = base_url.rstrip("/")
        self.page_size = page_size
        self.max_pages = max_pages
        self.sleep_seconds = sleep_seconds
        self.token = token

        # cache in memoria
        self._cache_counts = {}

        # cache su file
        self.cache_dir = Path(cache_dir) / "openaire"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------

    def _clean_keyword(self, kw: str) -> str:
        """
        Pulisce keyword per evitare errori API
        """
        kw = kw.strip()

        # rimuove contenuto tra parentesi
        kw = re.sub(r"\(.*?\)", "", kw)

        # lascia solo caratteri base
        kw = re.sub(r"[^a-zA-Z0-9\s]", "", kw)

        # normalizza spazi
        kw = " ".join(kw.split())

        return kw

    # -------------------------------------------------------

    def _cache_path(self, keyword: str) -> Path:
        """
        genera path cache basato su hash keyword
        """
        h = hashlib.md5(keyword.encode()).hexdigest()
        return self.cache_dir / f"{h}.json"

    # -------------------------------------------------------

    def _load_cache(self, keyword: str):

        p = self._cache_path(keyword)

        if p.exists():
            try:
                return json.loads(p.read_text())
            except:
                return None

        return None

    # -------------------------------------------------------

    def _save_cache(self, keyword: str, data: dict):

        p = self._cache_path(keyword)

        try:
            p.write_text(json.dumps(data))
        except:
            pass

    # -------------------------------------------------------

    def _get(self, params: dict):
        """
        chiamata GET con retry leggero
        """

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

    # -------------------------------------------------------

    def _count(self, field: str, keyword: str) -> int:
        """
        Conta occorrenze di keyword in un campo OpenAIRE
        """

        kw = self._clean_keyword(keyword)

        if not kw or kw.strip() == "":
            print(f"[DEBUG] Keyword scartata (vuota): '{keyword}'")
            return 0

        params = {
            field: kw,
            "page": 1,
            "pageSize": 10
        }

        try:
            
            data = self._get(params)
            return data.get("total", 0)

            # OpenAIRE di solito restituisce "total"
            #if isinstance(data, dict):
                #return data.get("total", 0)

            #return 0

        except Exception as e:

            print(f"[WARNING] OpenAIRE errore per '{kw}': {e}")

            return 0

    # -------------------------------------------------------

    def count_all_fields(self, keyword: str) -> dict:
        """
        Conta keyword nei campi principali OpenAIRE
        con caching
        """

        kw = self._clean_keyword(keyword)

        if not kw:
            return {
                "count_title": 0,
                "count_desc": 0
            }

        # cache RAM
        if kw in self._cache_counts:
            return self._cache_counts[kw]

        # cache file
        cached = self._load_cache(kw)

        if cached:
            self._cache_counts[kw] = cached
            return cached

        # query API
        result = {
            "count_title": self._count("mainTitle", kw),
            "count_desc": self._count("description", kw),
        }

        # salva cache
        self._cache_counts[kw] = result
        self._save_cache(kw, result)

        time.sleep(self.sleep_seconds)

        return result


"""
# Client per interrogare l'API di OpenAIRE, con supporto per paginazione, rate limiting e caching su filesystem


from typing import Dict
import time
import requests
from pathlib import Path
import hashlib, json
import re 

def _clean_keyword(self, kw: str) -> str:

    #Pulisce keyword per query OpenAIRE

    kw = kw.strip()

    # rimuove parentesi e contenuto
    kw = re.sub(r"\(.*?\)", "", kw)

    # lascia solo lettere e numeri base
    kw = re.sub(r"[^a-zA-Z0-9\s]", "", kw)

    # normalizza spazi
    kw = " ".join(kw.split())

    return kw

class OpenAIREClient:
    def __init__(self, base_url: str, page_size: int, max_pages: int, sleep_seconds: float, cache_dir: str, token: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.page_size = page_size
        self.max_pages = max_pages
        self.sleep = sleep_seconds
        self.token = token or ''
        self.cache_dir = Path(cache_dir) / 'openaire'
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{hashlib.md5(key.encode('utf-8')).hexdigest()}.json"

    def _get(self, params: Dict) -> Dict:
        headers = {'accept': 'application/json'}
        if self.token:
            headers['Authorization'] = f"Bearer {self.token}"
        r = requests.get(self.base_url, params=params, headers=headers, timeout=60)
        r.raise_for_status()
        return r.json()

    def _count(self, field: str, keyword: str) -> int:
        # Prova a usare cache per ogni tripletta (field, keyword)
        ck = json.dumps({'f': field, 'k': keyword, 'ps': self.page_size})
        cp = self._cache_path(ck)
        if cp.exists():
            try:
                cached = json.loads(cp.read_text(encoding='utf-8'))
                return cached['count']
            except Exception:
                pass
        page = 0
        total = 0
        while page < self.max_pages:
            params = {field: keyword, 'page': page, 'size': self.page_size}
            data = self._get(params)
            items = data.get('items') or data.get('results') or []
            total += len(items)
            # Se l'API esponesse un "total" lo useremmo direttamente; pagina fino a esaurimento
            if len(items) < self.page_size:
                break
            page += 1
            time.sleep(self.sleep)
        cp.write_text(json.dumps({'count': total}), encoding='utf-8')
        return total

    def count_all_fields(self, keyword: str) -> Dict[str, int]:
        return {
            'count_title': self._count('mainTitle', keyword),
            'count_description': self._count('description', keyword),
            'count_subjects': self._count('subjects', keyword)
        }
"""