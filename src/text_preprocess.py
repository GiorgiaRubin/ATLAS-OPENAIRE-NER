# Text normalization, to improve the quality of keyword and NER extraction

import re, unicodedata
from typing import Dict

_WS_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize('NFC', text)
    t = t.replace(' ', ' ')
    t = _WS_RE.sub(' ', t)
    return t.strip()


def preprocess_record(rec: Dict, lang_hint: str | None = None) -> Dict:
    title = normalize_text(rec.get('title') or '')
    desc = normalize_text(rec.get('desc') or '')
    return {**rec, 'title': title, 'desc': desc, 'lang': lang_hint}
