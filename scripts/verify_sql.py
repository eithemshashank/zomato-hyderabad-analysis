"""Run sql/queries.sql against the processed CSVs using SQLite (same results as MySQL 8 for these queries).
YEAR(x) is mapped to strftime so the file stays MySQL-native."""
import re, sqlite3
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; P = ROOT / "data" / "processed"
con = sqlite3.connect(":memory:")
for t in ["restaurants", "reviews", "restaurant_collections", "restaurant_cuisines"]:
    pd.read_csv(P / f"{t}.csv").to_sql(t, con, index=False)
con.execute("UPDATE reviews SET has_pictures = CASE WHEN has_pictures IN ('True', 1) THEN 1 ELSE 0 END")
sql = (ROOT / "sql" / "queries.sql").read_text()
sql = re.sub(r"YEAR\((\w+)\)", r"CAST(strftime('%Y', \1) AS INT)", sql)
for i, q in enumerate([s for s in sql.split(";") if s.strip()], 1):
    print(f"--- query {i}"); print(pd.read_sql_query(q, con).to_string(index=False))
