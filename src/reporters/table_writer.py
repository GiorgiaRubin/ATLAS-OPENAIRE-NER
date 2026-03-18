# Writer per salvare i risultati in CSV e XLSX, con supporto per pandas se disponibile, altrimenti fallback a CSV minimale


from typing import List, Dict
from pathlib import Path

try:
    import pandas as pd
except Exception:
    pd = None


def write_outputs(rows: List[Dict], out_csv: str, out_xlsx: str | None = None):
    Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
    if pd is not None:
        df = pd.DataFrame(rows)
        df.to_csv(out_csv, index=False)
        if out_xlsx:
            df.to_excel(out_xlsx, index=False, engine='openpyxl')
    else:
        # fallback CSV minimale
        import csv
        if rows:
            with open(out_csv, 'w', encoding='utf-8', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
