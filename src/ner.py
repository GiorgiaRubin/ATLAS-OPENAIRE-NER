# Named Entity extraction from text, with minimal fallback if spaCy is not available

from src.logging_conf import setup_logging
from typing import List, Dict

try:
    import spacy
except Exception:
    spacy = None


class NERExtractor:
    def __init__(self, model_name: str = 'it_core_news_lg'):  # model config
        self.model_name = model_name
        self.nlp = None
        if spacy is not None:
            try:
                self.nlp = spacy.load(model_name)
            except Exception:
                self.nlp = None

    def extract(self, title: str, desc: str, debug: bool = False) -> List[Dict]:
        log = setup_logging()
        text = " -- ".join([t for t in [title, desc] if t])
        log.info(f"Extracting NER from text -- {text}")

        ents: List[Dict] = []

        if self.nlp is None:
            log.info("spaCy model not available, skipping NER extraction.")
            return ents

        doc = self.nlp(text)

        for e in doc.ents:
            ents.append({
                'text': e.text,
                'label': e.label_,
                'lemma': e.lemma_ if hasattr(e, 'lemma_') else e.text,
                'score': getattr(e, 'score', 1.0)
            })

        log.info("\n=== NER OUTPUT ===")
        for e in ents:
            log.info(f"- TEXT: '{e['text']}' | LEMMA: '{e['lemma']}' | LABEL: {e['label']}")
        log.info("==================\n")

        return ents
