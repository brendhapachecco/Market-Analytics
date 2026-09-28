"""
generate_sample_data.py
------------------------
Gera um dataset SINTÉTICO de demonstração, com o mesmo schema que
collect_eures.py e collect_sepe.py produzem, para que o restante do
pipeline (limpeza, banco SQL, dashboard) possa ser executado e
demonstrado de ponta a ponta mesmo sem acesso à internet no momento da
coleta real.

ATENÇÃO: os dados aqui gerados NÃO são anúncios reais de vagas. Servem
apenas para popular o pipeline com um volume e uma distribuição
plausíveis. Antes de qualquer uso analítico real, substitua os arquivos
em data/raw/ pela saída de collect_eures.py e collect_sepe.py executados
com acesso à internet.
"""

import csv
import datetime as dt
import random
from pathlib import Path

random.seed(42)

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sample_postings_raw.csv"

FIELDNAMES = [
    "source",
    "source_url",
    "job_title",
    "company",
    "city",
    "region",
    "technologies_raw",
    "experience_raw",
    "work_mode_raw",
    "salary_raw",
    "posted_date",
    "collected_date",
]

CITY_REGION = {
    "Madrid": "Comunidad de Madrid",
    "Barcelona": "Cataluña",
    "Valencia": "Comunidad Valenciana",
    "Malaga": "Andalucía",
    "A Coruna": "Galicia",
}

# Peso relativo de vagas por cidade (Madrid e Barcelona concentram mais vagas tech).
CITY_WEIGHTS = {"Madrid": 0.38, "Barcelona": 0.30, "Valencia": 0.14, "Malaga": 0.11, "A Coruna": 0.07}

JOB_TITLES = {
    "Data": [
        "Data Analyst", "Analista de Datos", "Data Engineer", "Ingeniero de Datos",
        "Data Scientist", "Científico de Datos", "BI Analyst", "Analista BI",
        "Machine Learning Engineer",
    ],
    "Software Engineering": [
        "Software Engineer", "Ingeniero de Software", "Backend Developer",
        "Desarrollador Backend", "Frontend Developer", "Desarrollador Frontend",
        "Full Stack Developer", "DevOps Engineer", "QA Engineer", "Ingeniero QA",
    ],
}

TECH_POOL = {
    "Data": ["Python", "SQL", "Power BI", "Tableau", "Spark", "Airflow", "AWS", "Azure",
             "GCP", "Excel", "R", "Snowflake", "dbt", "Looker", "Databricks"],
    "Software Engineering": ["Java", "Python", "JavaScript", "TypeScript", "React", "Angular",
                              "Spring Boot", "Docker", "Kubernetes", "AWS", "Azure", "SQL",
                              "Node.js", ".NET", "Git", "CI/CD"],
}

EXPERIENCE_LEVELS = ["Sin experiencia", "1-2 años", "3-5 años", "5+ años"]
WORK_MODES = ["Presencial", "Híbrido", "Remoto"]
COMPANIES = [
    "Indra", "Telefónica", "BBVA", "CaixaBank", "Amadeus", "Seat", "Mango",
    "Glovo", "Cabify", "Naturgy", "Iberdrola", "Accenture España", "NTT Data",
    "Everis", "Zara (Inditex)", "Wallapop", "Typeform", "Factorial", "Startup Local S.L.",
]

SOURCES = ["EURES", "SEPE"]

N_ROWS = 620
START_DATE = dt.date(2026, 3, 1)
END_DATE = dt.date(2026, 8, 31)


def random_date(start: dt.date, end: dt.date) -> dt.date:
    delta = (end - start).days
    return start + dt.timedelta(days=random.randint(0, delta))


def weighted_city() -> str:
    cities = list(CITY_WEIGHTS.keys())
    weights = list(CITY_WEIGHTS.values())
    return random.choices(cities, weights=weights, k=1)[0]


def build_row(idx: int) -> dict:
    area = random.choice(["Data", "Software Engineering"])
    city = weighted_city()
    title = random.choice(JOB_TITLES[area])
    n_techs = random.randint(2, 5)
    techs = random.sample(TECH_POOL[area], k=min(n_techs, len(TECH_POOL[area])))
    posted = random_date(START_DATE, END_DATE)
    collected = posted + dt.timedelta(days=random.randint(0, 5))

    # ~30% dos anúncios não divulgam salário (comum no mercado espanhol).
    if random.random() < 0.30:
        salary_raw = ""
    else:
        base = random.randint(22, 65) * 1000
        spread = random.randint(0, 15) * 1000
        salary_raw = f"{base} - {base + spread} EUR/año"

    source = random.choice(SOURCES)
    return {
        "source": source,
        "source_url": f"https://example-{source.lower()}.es/oferta/{idx}",
        "job_title": title,
        "company": random.choice(COMPANIES),
        "city": city,
        "region": CITY_REGION[city],
        "technologies_raw": ", ".join(techs),
        "experience_raw": random.choice(EXPERIENCE_LEVELS),
        "work_mode_raw": random.choice(WORK_MODES),
        "salary_raw": salary_raw,
        "posted_date": posted.isoformat(),
        "collected_date": collected.isoformat(),
    }


def generate(n: int = N_ROWS) -> list[dict]:
    return [build_row(i) for i in range(1, n + 1)]


def save(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Salvo: {path} ({len(rows)} registros sintéticos)")


if __name__ == "__main__":
    rows = generate()
    save(rows, OUTPUT_PATH)
