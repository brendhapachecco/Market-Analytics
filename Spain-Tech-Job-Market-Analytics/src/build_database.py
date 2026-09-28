"""
build_database.py
------------------
Cria o banco SQLite database/spain_tech_jobs.db a partir de:
- sql/schema.sql
- data/processed/job_postings_clean.csv
- data/processed/job_skills_long.csv

Uso: python src/build_database.py
"""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "sql" / "schema.sql"
POSTINGS_CSV = ROOT / "data" / "processed" / "job_postings_clean.csv"
SKILLS_LONG_CSV = ROOT / "data" / "processed" / "job_skills_long.csv"
DB_PATH = ROOT / "database" / "spain_tech_jobs.db"


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 1) Cria o schema
    cur.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # 2) Carrega dados processados
    postings = pd.read_csv(POSTINGS_CSV)
    skills_long = pd.read_csv(SKILLS_LONG_CSV)

    # 3) Popula dimensão cities
    cities_df = postings[["city", "region"]].drop_duplicates().rename(
        columns={"city": "city_name"}
    )
    cities_df.to_sql("cities", conn, if_exists="append", index=False)

    city_id_map = dict(
        cur.execute("SELECT city_name, city_id FROM cities").fetchall()
    )

    # 4) Popula dimensão skills
    unique_skills = sorted(skills_long["skill"].dropna().unique())
    cur.executemany(
        "INSERT INTO skills (skill_name) VALUES (?)",
        [(s,) for s in unique_skills],
    )
    conn.commit()
    skill_id_map = dict(cur.execute("SELECT skill_name, skill_id FROM skills").fetchall())

    # 5) Popula fato postings
    postings_out = postings.copy()
    postings_out["city_id"] = postings_out["city"].map(city_id_map)
    postings_out["salary_disclosed"] = postings_out["salary_disclosed"].astype(bool).astype(int)

    postings_final = postings_out.rename(columns={"job_title": "job_title_raw"})[
        [
            "posting_id", "source", "source_url", "job_title_raw", "job_title_standardized",
            "professional_area", "company", "city_id", "experience_level", "work_mode",
            "salary_min", "salary_max", "salary_disclosed", "posted_date", "collected_date",
        ]
    ]
    postings_final.to_sql("postings", conn, if_exists="append", index=False)

    # 6) Popula ponte posting_skills
    bridge = skills_long.copy()
    bridge["skill_id"] = bridge["skill"].map(skill_id_map)
    bridge = bridge.dropna(subset=["skill_id"])[["posting_id", "skill_id"]].drop_duplicates()
    bridge.to_sql("posting_skills", conn, if_exists="append", index=False)

    conn.commit()

    # Conferência rápida
    n_postings = cur.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
    n_skills = cur.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    n_bridge = cur.execute("SELECT COUNT(*) FROM posting_skills").fetchone()[0]
    n_cities = cur.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
    print(f"Banco criado em: {DB_PATH}")
    print(f"  cidades: {n_cities} | vagas: {n_postings} | competências: {n_skills} | vínculos vaga-competência: {n_bridge}")

    conn.close()


if __name__ == "__main__":
    main()
