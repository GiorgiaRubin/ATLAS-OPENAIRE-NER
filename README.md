# ATLAS-OPENAIRE-NER

Pipeline to extract title/description from resources in the ***ATLAS Knowledge Graph*** (SPARQL),
perform ***NER/Keyphrase extraction***, search for ***keywords*** in the ***OpenAIRE Graph API***, and generate a
***mapping*** table of ATLAS → OpenAIRE resources.


## Requirements (recommended)
- Python 3.10+
- `pip install -r requirements.txt`
- spaCy models (e.g.):
  - `python -m spacy download it_core_news_sm`
  - `python -m spacy download en_core_web_sm`

## Run
```bash
python scripts/run_pipeline.py --config config/config.yml
```

## Output
- CSV/Excel in `data/reports/`
- Cache in `data/cache/`

## Repository structure
```
├─ README.md 
├─ requirements.txt 
├─ pyproject.toml 
├─ config/ 
│ ├─ config.yml # ← copialo configuration file 
│ └─ keyword_policies.yml # optional (domain whitelist/blacklist) 
├─ src/ 
│ ├─ __init__.py 
│ ├─ logging_conf.py 
│ ├─ config_loader.py 
│ ├─ atlas_client.py # SPARQL (ATLAS) + cache 
│ ├─ text_preprocess.py # text normalization
│ ├─ ner.py # NER spaCy + noun chunks 
│ ├─ keyphrases.py # optional YAKE + simple fallback
│ ├─ keyword_policy.py # keywords selection/deduplicaion
│ ├─ keyword_registry.py # avoids duplicate calls to OpenAIRE
│ ├─ openaire_client.py # OpenAIRE Graph API calls + cache 
│ ├─ aggregator.py 
│ └─ reporters/ 
│   └─ table_writer.py # CSV/Excel 
├─ scripts/ 
│ └─ run_pipeline.py # orchestrator
├─ data/ 
│ ├─ cache/ 
│ └─ reports/ 
├─ tests/ 
│ └─ test_placeholder.py 
└─ docs/ 
  └─ flow.md
```
