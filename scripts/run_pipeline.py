# Main script to run the pipeline for keyword extraction and enrichment
# from ATLAS resources, with CSV/XLSX output for cross‑graph signal
# alignment between ATLAS and OpenAIRE.

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

    # --- init components ---
    atlas = AtlasClient(
        cfg.atlas['sparql_endpoint'],
        cfg.cache['dir'],
        cfg.cache.get('ttl_days', 7)
    )

    ner = NERExtractor(cfg.nlp.get('spacy_model', 'it_core_news_lg'))  # model configuration
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

    # --- extraction and keyword registration ---

    for rec in atlas.fetch_resources(
        tpred, dpred, classes, langs, page_size=page_size
    ):
        cnt += 1

        if not (rec.get('title') or rec.get('desc')):
            continue

        # --- preprocess ---
        prec = preprocess_record(rec)

        # --- NER ---
        ents = ner.extract(prec['title'], prec['desc'], debug=True)

        # --- enrich with keyphrases if enabled ---
        if cfg.nlp.get('use_keyphrases', True):
            text = (prec.get('title') or '') + " " + (prec.get('desc') or '')
            kps = extract_keyphrases(text, topk=10)
            ents.extend(
                {'text': kp, 'label': 'KEYPHRASE', 'lemma': kp}
                for kp in kps
            )

        selected = policy.select(ents)

        log.info(f"[DEBUG] Record {cnt}")
        log.info(f"Keywords after policy: {len(selected)}")

        # --- save global keywords ---
        registry.add_many(selected)

        # --- save data without enrichment ---
        for kw in selected:
            agg.add_partial(
                prec['res'],
                prec.get('title') or '',
                kw,
                'KEYWORD',
                'NER+KP'
            )

        if cnt % 20 == 0:
            log.info(f"Processed {cnt} records")

    # --- OpenAIRE enrichment ---

    all_keywords = registry.all()
    log.info(f"Total unique keywords: {len(all_keywords)}")

    keyword_counts = {}

    for i, kw in enumerate(all_keywords):
        try:
            keyword_counts[kw] = openaire.count_all_fields(kw)

        except Exception as e:
            log.warning(f"OpenAIRE error for '{kw}': {e}")
            keyword_counts[kw] = {
                'count_title': 0,
                'count_desc': 0
            }

        if i % 50 == 0:
            log.info(f"OpenAIRE progress: {i}/{len(all_keywords)}")

    # --- join results ---

    agg.enrich(keyword_counts)

    rows = agg.result()

    write_outputs(
        rows,
        cfg.report['out_csv'],
        cfg.report.get('out_xlsx')
    )

    log.info(f"Completed. Output rows: {len(rows)}")


if __name__ == '__main__':
    main()