# Policy for filtering and deduplicating extracted keywords,
# with support for whitelist/blacklist, stopwords, and fuzzy matching

from typing import List, Dict, Set
from rapidfuzz import fuzz


class KeywordPolicy:
    def __init__(self, cfg: dict):
        self.whitelist = set(cfg.get('whitelist_labels', []))
        self.blacklist = set(cfg.get('blacklist_labels', []))
        self.min_len = cfg.get('min_len', 3)
        self.topk = cfg.get('topk_per_doc', 15)
        self.use_fuzzy = cfg.get('use_fuzzy_dedup', True)
        self.fuzzy_threshold = cfg.get('fuzzy_threshold', 90)
        self.stopwords: Set[str] = set(map(str.lower, cfg.get('stopwords', [])))

    def _accept_label(self, label: str) -> bool:
        # whitelist must NOT eliminate everything
        if self.whitelist:
            if label not in self.whitelist and label != 'NOUN_CHUNK':
                return False

        if label in self.blacklist:
            return False

        return True

    def select(self, candidates: List[Dict]) -> List[str]:
        # filter by label/length/stopwords
        out: List[str] = []
        for c in candidates:
            txt = (c.get('lemma') or c.get('text') or '').strip()
            if len(txt) < self.min_len:
                continue
            if not self._accept_label(c.get('label', '')):
                continue
            if txt.lower() in self.stopwords:
                continue
            out.append(txt)

        # DEBUG
        print(f"[DEBUG POLICY] candidates: {len(candidates)} → after base filter: {len(out)}")

        # fallback: NEVER return an empty list
        if not out:
            fallback = [
                (c.get('lemma') or c.get('text') or '').strip()
                for c in candidates
                if (c.get('lemma') or c.get('text'))
            ]
            fallback = [k for k in fallback if len(k) >= self.min_len]

            print("[WARNING] Policy filtered everything → internal fallback")
            return fallback[: self.topk]

        # simple deduplication
        dedup: List[str] = []
        for k in out:
            if not any(k.lower() == d.lower() for d in dedup):
                dedup.append(k)

        # fuzzy deduplication
        if self.use_fuzzy:
            final: List[str] = []
            for k in dedup:
                if not any(fuzz.token_set_ratio(k, f) >= self.fuzzy_threshold for f in final):
                    final.append(k)
            dedup = final

        return dedup[: self.topk]
