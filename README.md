
# ATLAS-OPENAIRE-NER

Pipeline per estrarre titolo/descrizione da risorse del Knowledge Graph **ATLAS** (SPARQL),
eseguire **NER/Keyphrase**, cercare le **keywords** nell'**OpenAIRE Graph API** e generare una
tabella di mapping delle risorse ATLAS→OpenAIRE.


## Requisiti (consigliati)
- Python 3.10+
- `pip install -r requirements.txt`
- Modelli spaCy (es.):
  - `python -m spacy download it_core_news_sm`
  - `python -m spacy download en_core_web_sm`

## Esecuzione
```bash
python scripts/run_pipeline.py --config config/config.yml
```

## Output
- CSV/Excel in `data/reports/`
- Cache in `data/cache/`

## Struttura cartella
```
├─ README.md 
├─ requirements.txt 
├─ pyproject.toml 
├─ config/ 
│ ├─ config.example.yml # ← copialo in config.yml e personalizza 
│ └─ keyword_policies.yml # opzionale (whitelist/blacklist dominio) 
├─ src/atlas_openaire_ner/ 
│ ├─ __init__.py 
│ ├─ logging_conf.py 
│ ├─ config_loader.py 
│ ├─ atlas_client.py # SPARQL (ATLAS) + cache 
│ ├─ text_preprocess.py # normalizzazione testo 
│ ├─ ner.py # NER spaCy + noun chunks 
│ ├─ keyphrases.py # YAKE opzionale + fallback semplice 
│ ├─ keyword_policy.py # selezione/dedup keywords
│ ├─ keyword_registry.py # evita chiamate duplicate a OpenAIRE 
│ ├─ openaire_client.py # chiamate Graph API OpenAIRE + cache 
│ ├─ aggregator.py 
│ └─ reporters/ 
│   └─ table_writer.py # CSV/Excel 
├─ scripts/ 
│ └─ run_pipeline.py # orchestratore
├─ data/ 
│ ├─ cache/ 
│ └─ reports/ 
├─ tests/ 
│ └─ test_placeholder.py 
└─ docs/ 
  └─ flow.md
```
