# Estrazione di Named Entities da un testo, con fallback minimale se Spacy non è disponibile


from typing import List, Dict

try:
    import spacy
except Exception:
    spacy = None

class NERExtractor:
    def __init__(self, model_name: str = 'it_core_news_sm'):
        self.model_name = model_name
        self.nlp = None
        if spacy is not None:
            try:
                self.nlp = spacy.load(model_name)
            except Exception:
                self.nlp = None

    def extract(self, title: str, desc: str) -> List[Dict]:
        text = "".join([t for t in [title, desc] if t])
        ents: List[Dict] = []
        if self.nlp is None:
            return ents
        doc = self.nlp(text)
        for e in doc.ents:
            ents.append({
                'text': e.text,
                'label': e.label_,
                'lemma': e.lemma_ if hasattr(e, 'lemma_') else e.text,
                'score': getattr(e, 'score', 1.0)
            })
        # semplice estrazione di noun chunks come fallback keyword-like
        for nc in getattr(doc, 'noun_chunks', []):
            ents.append({'text': nc.text, 'label': 'NOUN_CHUNK', 'lemma': nc.lemma_ if hasattr(nc, 'lemma_') else nc.text, 'score': 0.5})
        return ents
