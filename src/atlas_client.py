# Client per interrogare l'endpoint SPARQL di ATLAS, con caching su filesystem per migliorare le prestazioni


from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Iterator, Dict, List, Optional
import hashlib, json
from pathlib import Path
from time import time

class AtlasClient:
    def __init__(self, endpoint: str, cache_dir: str, ttl_days: int = 7):
        self.sparql = SPARQLWrapper(endpoint)
        self.sparql.setReturnFormat(JSON)
        self.cache_dir = Path(cache_dir) / 'atlas'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_days * 86400

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{hashlib.md5(key.encode('utf-8')).hexdigest()}.json"

    def _get_cached(self, key: str):
        p = self._cache_path(key)
        if p.exists() and (time() - p.stat().st_mtime) < self.ttl:
            return json.loads(p.read_text(encoding='utf-8'))
        return None

    def _set_cache(self, key: str, value):
        p = self._cache_path(key)
        p.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    
    def _build_query(
        self,
        title_preds: List[str],
        desc_preds: List[str],
        classes: Optional[List[str]],
        page_size: int,
        offset: int,
        preferred_langs: List[str]
    ):
        # --- Predicati titolo/descrizione ---
        title_values = " ".join(f"<{p}>" for p in title_preds)
        desc_values  = " ".join(f"<{p}>" for p in desc_preds)

        # --- Filtro classi RDF opzionale ---
        class_filter = ""
        if classes:
            class_values = " ".join(f"<{c}>" for c in classes)
            class_filter = f"?res a ?type . VALUES ?type {{ {class_values} }}"

        # --- Filtri lingua compatibili con Blazegraph ---
        lang_filter = ""
        if preferred_langs:
            conditions_title = " || ".join(
                f'langMatches(lang(?title), "{l}")' for l in preferred_langs
            )
            conditions_desc = " || ".join(
                f'langMatches(lang(?desc), "{l}")' for l in preferred_langs
            )

            lang_filter = f"""
                FILTER( !BOUND(?title) || {conditions_title} )
                FILTER( !BOUND(?desc)  || {conditions_desc} )
            """

        # --- Query SPARQL ---
        q = f"""
            PREFIX dcterms: <http://purl.org/dc/terms/>
            PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema:  <http://schema.org/>
            PREFIX bibo:    <http://purl.org/ontology/bibo/>

            SELECT ?res ?title ?desc
            WHERE {{
                {class_filter}

                OPTIONAL {{
                    ?res ?pTitle ?title .
                    VALUES ?pTitle {{ {title_values} }}
                }}

                OPTIONAL {{
                    ?res ?pDesc ?desc .
                    VALUES ?pDesc {{ {desc_values} }}
                }}

                {lang_filter}
            }}
            LIMIT {page_size} OFFSET {offset}
            """
        

        print("\n=== SPARQL QUERY ===")
        print(q)
        print("====================\n")


        return q


    def fetch_resources(self, title_preds: List[str], desc_preds: List[str], classes: Optional[List[str]], preferred_langs: List[str], page_size: int = 200) -> Iterator[Dict]:
        offset = 0
        while True:
            q = self._build_query(title_preds, desc_preds, classes, page_size, offset, preferred_langs)
            ck = f"atlas:{offset}:{page_size}:{hashlib.md5(q.encode()).hexdigest()}"
            cached = self._get_cached(ck)
            if cached is None:
                self.sparql.setQuery(q)
                res = self.sparql.query().convert()
                self._set_cache(ck, res)
            else:
                res = cached
            rows = res.get('results', {}).get('bindings', [])
            if not rows:
                break
            for b in rows:
                yield {
                    'res': b.get('res', {}).get('value'),
                    'title': b.get('title', {}).get('value'),
                    'desc': b.get('desc', {}).get('value'),
                }
            offset += page_size
