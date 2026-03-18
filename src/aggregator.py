# Aggregator migliorato: separa raccolta e enrichment
from typing import List, Dict


class Aggregator:

    def __init__(self):
        self.rows: List[Dict] = []

    def add_partial(self, atlas_id: str, titolo: str, keyword: str, tipo: str, metodo: str):
        """
        Salva dati senza enrichment OpenAIRE
        """
        self.rows.append({
            'atlas_id': atlas_id,
            'titolo_atlas': titolo,
            'keyword': keyword,
            'tipo_entita': tipo,
            'metodo': metodo
        })

    def enrich(self, keyword_counts: Dict[str, Dict]):
        """
        Aggiunge counts OpenAIRE alle righe già raccolte
        """
        for row in self.rows:
            kw = row['keyword'].lower()
            counts = keyword_counts.get(kw, {})

            row.update({
                'count_title': counts.get('count_title', 0),
                'count_desc': counts.get('count_desc', 0),
            })

    def result(self) -> List[Dict]:
        return self.rows


"""
# Aggregator per aggregare i risultati in una struttura tabellare (lista di dizionari)


from typing import List, Dict

class Aggregator:                   #class per aggregare i risultati in una struttura tabellare (lista di dizionari) 
    def __init__(self):
        self.rows: List[Dict] = []

    def add(self, atlas_id: str, titolo: str, keyword: str, tipo: str, metodo: str, counts: Dict[str, int]):
        if not keyword:
            return

        self.rows.append({
            'atlas_id': atlas_id,               #posso scegliere quali campi includere, non necessariamente questi.
            'titolo_atlas': titolo,
            'keyword': keyword,
            'tipo_entita': tipo,
            'metodo': metodo,
            **counts
        })

    def result(self) -> List[Dict]:
        return self.rows
"""