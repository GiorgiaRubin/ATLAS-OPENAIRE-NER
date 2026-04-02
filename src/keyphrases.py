# Extraction of key phrases from text, with minimal fallback if YAKE is not available


from typing import List

try:
    import yake
except Exception:
    yake = None


def extract_keyphrases(text: str, topk: int = 10, lan: str = 'it') -> List[str]:
    if not text:
        return []
    if yake is None:
        # minimal fallback: returns unique words longer than 4 characters
        toks = [w.strip('.,;:!?()[]') for w in text.split()]  # noqa
        toks = [t for t in toks if len(t) >= 5]
        uniq = []
        for t in toks:
            if t.lower() not in {u.lower() for u in uniq}:
                uniq.append(t)
            if len(uniq) >= topk:
                break
        return uniq
    kw = yake.KeywordExtractor(lan=lan, n=3, top=topk)
    return [k for k, s in kw.extract_keywords(text)]
