# Script principale per eseguire la pipeline di estrazione e arricchimento keyword da risorse ATLAS, con output in CSV/XLSX per cross‑graph signal alignment ATLAS-OpenAIRE


import argparse
import sys
from pathlib import Path        
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.config_loader import load_config
from src.logging_conf import setup_logging
from src.atlas_client import AtlasClient
from src.text_preprocess import preprocess_record
from src.ner import NERExtractor
from src.keyphrases import extract_keyphrases
from src.keyword_policy import KeywordPolicy
from src.openaire_client import OpenAIREClient
from src.aggregator import Aggregator
from src.keyword_registry import KeywordRegistry
from src.reporters.table_writer import write_outputs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()

    cfg = load_config(args.config)
    log = setup_logging()
    
    #--- init componenti ---
    atlas = AtlasClient(cfg.atlas['sparql_endpoint'], cfg.cache['dir'], cfg.cache.get('ttl_days', 7))
    ner = NERExtractor(cfg.nlp.get('spacy_model', 'it_core_news_sm'))
    policy = KeywordPolicy(cfg.policy)

    openaire = OpenAIREClient(
        base_url=cfg.openaire['base_url'],
        cache_dir=cfg.cache['dir']
    )

    agg = Aggregator()
    registry = KeywordRegistry()

    page_size = cfg.atlas.get('page_size', 200)
    classes = cfg.atlas.get('resource_classes')
    tpred = cfg.atlas['title_predicates']
    dpred = cfg.atlas['description_predicates']
    langs = cfg.atlas.get('preferred_langs', [])

    cnt = 0
    #debug_limit = 5  # mostra debug solo per i primi N record

    # ---ESTRAZIONE + REGISTRAZIONE KEYWORDS---

    for rec in atlas.fetch_resources(tpred, dpred, classes, langs, page_size=page_size):
        cnt += 1

        if not (rec.get('title') or rec.get('desc')):
            continue

        # ---Preprocess---
        prec = preprocess_record(rec)

        # ---NER---
        ents = ner.extract(prec['title'], prec['desc'], debug=True)

        # arricchisci con keyphrases se richiesto
        if cfg.nlp.get('use_keyphrases', True):
            text = (prec.get('title') or '') + " " + (prec.get('desc') or '')
            kps = extract_keyphrases(text, topk=10)
            ents.extend({'text': kp, 'label': 'KEYPHRASE', 'lemma': kp} for kp in kps)
            #from_lang = (langs[0] if langs else 'it')
            #text = "".join([prec.get('title') or '', prec.get('desc') or '']).strip()
            #kps = extract_keyphrases(text, topk=cfg.nlp.get('max_keyphrases_per_doc', 12), lan=from_lang)
            #ents.extend({'text': kp, 'label': 'KEYPHRASE', 'lemma': kp, 'score': 0.7} for kp in kps)

        selected = policy.select(ents)

        log.info(f"[DEBUG] Record {cnt}")
        log.info(f"Keywords dopo policy: {len(selected)}")

        # salva keyword globali
        registry.add_many(selected)

        # salva dati senza enrichment
        for kw in selected:
            agg.add_partial(
                prec['res'],
                prec.get('title') or '',
                kw,
                'KEYWORD',
                'NER+KP'
            )

        if cnt % 20 == 0:
            log.info(f"Processati {cnt} record")

    # =====================================================
    # 2️⃣ ENRICHMENT OPENAIRE (UNA VOLTA SOLA PER KEYWORD)
    # =====================================================

    all_keywords = registry.all()
    log.info(f"Keyword uniche totali: {len(all_keywords)}")

    keyword_counts = {}

    for i, kw in enumerate(all_keywords):

        try:
            keyword_counts[kw] = openaire.count_all_fields(kw)

        except Exception as e:
            log.warning(f"Errore OpenAIRE per '{kw}': {e}")
            keyword_counts[kw] = {
                'count_title': 0,
                'count_desc': 0
            }

        if i % 50 == 0:
            log.info(f"OpenAIRE progress: {i}/{len(all_keywords)}")

    # =====================================================
    # 3️⃣ JOIN RISULTATI
    # =====================================================

    agg.enrich(keyword_counts)

    rows = agg.result()

    write_outputs(rows, cfg.report['out_csv'], cfg.report.get('out_xlsx'))

    log.info(f"Completato. Righe output: {len(rows)}")


if __name__ == '__main__':
    main()
        
        
        
"""
        # --- DEBUG ---
        if cnt <= debug_limit:
            log.info(f"[DEBUG] Record {cnt}")
            log.info(f"Title: {prec.get('title')}")
            log.info(f"Entities estratte: {len(ents)}")

        #--- Policy ---   
        selected = policy.select(ents)

        if cnt <= debug_limit:
            log.info(f"Keywords dopo policy: {len(selected)}")

        # FALLBACK: se la policy elimina tutto, usa le prime entità
        if not selected:
            if cnt <= debug_limit:
                log.warning("Policy ha filtrato tutto → fallback attivo")

            selected = list({e['lemma'] for e in ents if e.get('lemma')})[:5]

        # --- AGGREGAZIONE ---
        for kw in selected:
            counts = openaire.count_all_fields(kw)
            # preferisci il label NER più frequente (semplice euristica)
            label = 'KEYWORD'
            metodo = 'NER+KP' if cfg.nlp.get('use_keyphrases', True) else 'NER'

            for e in ents:
                if e['lemma'] == kw or e['text'] == kw:
                    label = e.get('label', label)
                    break

            agg.add(prec['res'], prec.get('title') or '', kw, label, metodo, counts)

        if cnt % 20 == 0:
            log.info(f"Processate {cnt} risorse ATLAS")

    rows = agg.result()

    log.info(f"[DEBUG] Numero righe finali: {len(rows)}")

    write_outputs(rows, cfg.report['out_csv'], cfg.report.get('out_xlsx'))

    log.info(f"Completato. Righe output: {len(rows)}")

if __name__ == '__main__':
    main()
"""