# Aggregator separates collection and enrichment

from typing import List, Dict


class Aggregator:

    def __init__(self):
        self.rows: List[Dict] = []

    def add_partial(self, atlas_id: str, titolo: str, keyword: str, tipo: str, metodo: str):
        # Save data before OpenAIRE enrichment
        self.rows.append({
            'atlas_id': atlas_id,
            'titolo_atlas': titolo,
            'keyword': keyword,
            'tipo_entita': tipo,
            'metodo': metodo
        })

    def enrich(self, keyword_counts: Dict[str, Dict]):
        # Add OpenAIRE counts to the already collected rows
        for row in self.rows:
            kw = row['keyword'].lower()
            counts = keyword_counts.get(kw, {})

            row.update({
                'count_title': counts.get('count_title', 0),
                'count_desc': counts.get('count_desc', 0),
                'count_subject': counts.get('count_subject', 0)
            })

    def result(self) -> List[Dict]:
        return self.rows
