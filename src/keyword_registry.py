# Registry globale per evitare chiamate duplicate a OpenAIRE

class KeywordRegistry:

    def __init__(self):
        self._keywords = set()

    def add_many(self, keywords):
        for kw in keywords:
            if kw:
                self._keywords.add(kw.lower())

    def all(self):
        return list(self._keywords)