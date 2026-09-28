"""
clean_data.py
-------------
Lê os arquivos brutos em data/raw/ (saída de collect_eures.py,
collect_sepe.py e/ou generate_sample_data.py), padroniza cargos e
competências, remove duplicatas e trata anúncios sem salário informado.

Saída: data/processed/job_postings_clean.csv
       data/processed/job_skills_long.csv  (formato longo: 1 linha por
       combinação vaga x competência, usado para carregar o banco SQL)
"""

import glob
import re
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

# ---------------------------------------------------------------------------
# Dicionários de padronização
# ---------------------------------------------------------------------------
TITLE_STANDARDIZATION = {
    r"analista de datos": "Data Analyst",
    r"data analyst": "Data Analyst",
    r"analista bi": "BI Analyst",
    r"bi analyst": "BI Analyst",
    r"ingeniero de datos": "Data Engineer",
    r"data engineer": "Data Engineer",
    r"cient[ií]fico de datos": "Data Scientist",
    r"data scientist": "Data Scientist",
    r"machine learning": "Machine Learning Engineer",
    r"ingeniero de software": "Software Engineer",
    r"software engineer": "Software Engineer",
    r"desarrollador backend|backend developer": "Backend Developer",
    r"desarrollador frontend|frontend developer": "Frontend Developer",
    r"full ?stack": "Full Stack Developer",
    r"devops": "DevOps Engineer",
    r"ingeniero qa|qa engineer": "QA Engineer",
}

PROFESSIONAL_AREA_BY_TITLE = {
    "Data Analyst": "Dados",
    "BI Analyst": "Dados",
    "Data Engineer": "Dados",
    "Data Scientist": "Dados",
    "Machine Learning Engineer": "Dados",
    "Software Engineer": "Engenharia de Software",
    "Backend Developer": "Engenharia de Software",
    "Frontend Developer": "Engenharia de Software",
    "Full Stack Developer": "Engenharia de Software",
    "DevOps Engineer": "Engenharia de Software",
    "QA Engineer": "Engenharia de Software",
}

# Normaliza grafias diferentes da mesma tecnologia.
SKILL_ALIASES = {
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    ".net": ".NET",
    "dotnet": ".NET",
    "ci/cd": "CI/CD",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "sql": "SQL",
    "python": "Python",
    "java": "Java",
    "react": "React",
    "angular": "Angular",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "spring boot": "Spring Boot",
    "spring": "Spring Boot",
    "spark": "Spark",
    "airflow": "Airflow",
    "excel": "Excel",
    "r": "R",
    "snowflake": "Snowflake",
    "dbt": "dbt",
    "looker": "Looker",
    "databricks": "Databricks",
    "tableau": "Tableau",
    "git": "Git",
}

WORK_MODE_MAP = {
    "presencial": "Presencial",
    "híbrido": "Híbrido",
    "hibrido": "Híbrido",
    "remoto": "Remoto",
}


def load_raw() -> pd.DataFrame:
    files = glob.glob(str(RAW_DIR / "*.csv"))
    if not files:
        raise FileNotFoundError(
            f"Nenhum CSV bruto encontrado em {RAW_DIR}. "
            "Rode antes generate_sample_data.py (demo) ou os coletores reais."
        )
    frames = [pd.read_csv(f, dtype=str) for f in files]
    df = pd.concat(frames, ignore_index=True)
    print(f"Carregados {len(df)} registros brutos de {len(files)} arquivo(s): "
          f"{[Path(f).name for f in files]}")
    return df


def standardize_title(raw_title: str) -> str:
    if not isinstance(raw_title, str) or not raw_title.strip():
        return "Não classificado"
    t = raw_title.strip().lower()
    for pattern, standard in TITLE_STANDARDIZATION.items():
        if re.search(pattern, t):
            return standard
    return raw_title.strip().title()


def standardize_work_mode(raw_mode: str) -> str:
    if not isinstance(raw_mode, str) or not raw_mode.strip():
        return "Não informado"
    return WORK_MODE_MAP.get(raw_mode.strip().lower(), raw_mode.strip().title())


def parse_salary(raw_salary: str):
    """Extrai salario_min, salario_max e um booleano de divulgação."""
    if not isinstance(raw_salary, str) or not raw_salary.strip():
        return None, None, False
    nums = re.findall(r"\d+", raw_salary.replace(".", ""))
    nums = [int(n) for n in nums if len(n) >= 4]  # evita capturar "2026" isolado incorretamente também, mas ok p/ salários
    if not nums:
        return None, None, False
    if len(nums) == 1:
        return nums[0], nums[0], True
    return min(nums), max(nums), True


def split_skills(raw_skills: str) -> list[str]:
    if not isinstance(raw_skills, str) or not raw_skills.strip():
        return []
    parts = re.split(r"[;,/]", raw_skills)
    cleaned = []
    for p in parts:
        key = p.strip().lower()
        if not key:
            continue
        standardized = SKILL_ALIASES.get(key, p.strip())
        cleaned.append(standardized)
    # remove duplicatas preservando ordem
    seen = set()
    result = []
    for c in cleaned:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Padronizações básicas
    df["job_title_standardized"] = df["job_title"].apply(standardize_title)
    df["professional_area"] = df["job_title_standardized"].map(PROFESSIONAL_AREA_BY_TITLE).fillna("Não classificado")
    df["work_mode"] = df["work_mode_raw"].apply(standardize_work_mode)
    df["city"] = df["city"].fillna("Não informado").str.strip()
    df["region"] = df["region"].fillna("Não informado").str.strip()
    df["experience_level"] = df["experience_raw"].fillna("Não informado").str.strip()

    # Salário
    salary_parsed = df["salary_raw"].apply(parse_salary)
    df["salary_min"] = salary_parsed.apply(lambda x: x[0])
    df["salary_max"] = salary_parsed.apply(lambda x: x[1])
    df["salary_disclosed"] = salary_parsed.apply(lambda x: x[2])

    # Datas
    df["posted_date"] = pd.to_datetime(df["posted_date"], errors="coerce").dt.date
    df["collected_date"] = pd.to_datetime(df["collected_date"], errors="coerce").dt.date

    # Skills em lista (para o formato longo depois)
    df["technologies_list"] = df["technologies_raw"].apply(split_skills)

    # Identificador único da vaga
    df = df.reset_index(drop=True)
    df["posting_id"] = df.index + 1

    # -----------------------------------------------------------------
    # Deduplicação: mesma empresa + cargo padronizado + cidade + data de
    # publicação é tratado como o mesmo anúncio republicado.
    # -----------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(
        subset=["company", "job_title_standardized", "city", "posted_date"],
        keep="first",
    )
    after = len(df)
    print(f"Deduplicação: {before - after} registros duplicados removidos ({before} -> {after}).")

    return df


def build_long_skills(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        for skill in r["technologies_list"]:
            rows.append({"posting_id": r["posting_id"], "skill": skill})
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_raw()
    clean_df = clean(raw)

    final_cols = [
        "posting_id", "source", "source_url", "job_title", "job_title_standardized",
        "professional_area", "company", "city", "region", "experience_level",
        "work_mode", "salary_min", "salary_max", "salary_disclosed",
        "posted_date", "collected_date",
    ]
    clean_out = clean_df[final_cols]
    clean_out.to_csv(OUT_DIR / "job_postings_clean.csv", index=False)
    print(f"Salvo: {OUT_DIR / 'job_postings_clean.csv'} ({len(clean_out)} registros)")

    skills_long = build_long_skills(clean_df)
    skills_long.to_csv(OUT_DIR / "job_skills_long.csv", index=False)
    print(f"Salvo: {OUT_DIR / 'job_skills_long.csv'} ({len(skills_long)} registros)")

    # Aviso de qualidade: anúncios sem nenhuma tecnologia identificada
    n_sem_skill = (skills_long.groupby("posting_id").size().reindex(clean_out["posting_id"], fill_value=0) == 0).sum()
    if n_sem_skill:
        print(f"[AVISO] {n_sem_skill} vagas não têm nenhuma tecnologia identificada após o parsing.")


if __name__ == "__main__":
    main()
