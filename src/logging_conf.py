# Configurazione del logging, con rotazione dei file per evitare di occupare troppo spazio


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_file: str = "data/reports/pipeline.log"):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    fh = RotatingFileHandler(log_file, maxBytes=2*1024*1024, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger
