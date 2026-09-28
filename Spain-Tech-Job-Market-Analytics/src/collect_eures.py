"""
collect_eures.py
-----------------
Coleta anúncios de vagas do portal EURES (https://eures.europa.eu/) para
profissionais de Dados e Engenharia de Software na Espanha.

IMPORTANTE — LIMITAÇÃO DE AMBIENTE:
Este script foi desenvolvido para ser executado em uma máquina com acesso
irrestrito à internet. Ele NÃO foi executado dentro do ambiente que gerou
este projeto, pois esse ambiente possui acesso de rede restrito a um
conjunto fechado de domínios (não inclui eures.europa.eu). Por isso, o
dataset de demonstração incluído em data/raw/ foi gerado sinteticamente
por generate_sample_data.py, mantendo o mesmo schema que este coletor
produz. Para reproduzir a coleta real, rode este script em sua própria
máquina/servidor com `python src/collect_eures.py`.

O EURES não oferece uma API pública estável e documentada para todos os
países; a estrutura HTML pode mudar. Este script usa a API JSON interna
do portal (endpoint de busca), que é mais estável que fazer parsing de
HTML, mas ainda assim deve ser monitorada e ajustada se o portal mudar.

Uso responsável:
- Respeite o robots.txt e os Termos de Uso do EURES.
- Defina um intervalo (SLEEP_SECONDS) entre requisições.
- Colete apenas os campos necessários à pesquisa.
- Registre sempre a URL de origem e a data de coleta (rastreabilidade).
"""

import csv
import datetime as dt
import time
import sys
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE_SEARCH_URL = "https://eures.europa.eu/eures-apps/searchengine/page/search"
SLEEP_SECONDS = 2.0
TIMEOUT = 20
HEADERS = {
    "User-Agent": "Spain-Tech-Job-Market-Analytics/1.0 (uso academico; contato: substitua-por-seu-email)"
}

# Termos de busca relacionados às duas áreas profissionais do estudo.
SEARCH_TERMS = [
    "data analyst",
    "data engineer",
    "data scientist",
    "software engineer",
    "backend developer",
    "frontend developer",
    "devops engineer",
    "qa engineer",
    "machine learning engineer",
]

# Cidades / regiões-alvo (pode ser ampliado se houver volume de dados).
TARGET_CITIES = ["Madrid", "Barcelona", "Valencia", "Malaga", "A Coruna"]

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "eures_raw.csv"

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


def build_query_params(term: str, city: str, page: int = 0) -> dict:
    """Monta os parâmetros de busca para o endpoint do EURES.

    Os nomes exatos de parâmetros podem exigir ajuste caso a API do EURES
    seja alterada; consulte as chamadas feitas pelo próprio site (DevTools
    > Network) para atualizar este dicionário se necessário.
    """
    return {
        "text": term,
        "countryCode": "ES",
        "city": city,
        "page": page,
        "resultsPerPage": 50,
    }


def fetch_page(term: str, city: str, page: int) -> dict | None:
    params = build_query_params(term, city, page)
    try:
        resp = requests.get(BASE_SEARCH_URL, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        print(f"[AVISO] Falha ao buscar '{term}' em '{city}' (pág {page}): {exc}", file=sys.stderr)
        return None


def parse_results(payload: dict, term: str) -> list[dict]:
    """Extrai os campos de interesse de um payload de resposta do EURES.

    A estrutura exata do JSON deve ser validada contra uma resposta real,
    pois pode mudar entre versões do portal.
    """
    rows = []
    for item in payload.get("results", []):
        rows.append({
            "source": "EURES",
            "source_url": item.get("url", ""),
            "job_title": item.get("title", ""),
            "company": item.get("employerName", ""),
            "city": item.get("city", ""),
            "region": item.get("region", ""),
            "technologies_raw": item.get("skills", ""),
            "experience_raw": item.get("experienceRequired", ""),
            "work_mode_raw": item.get("workingArrangement", ""),
            "salary_raw": item.get("salary", ""),
            "posted_date": item.get("postingDate", ""),
            "collected_date": dt.date.today().isoformat(),
        })
    return rows


def collect() -> list[dict]:
    all_rows: list[dict] = []
    for term in SEARCH_TERMS:
        for city in TARGET_CITIES:
            page = 0
            while True:
                payload = fetch_page(term, city, page)
                if not payload:
                    break
                rows = parse_results(payload, term)
                if not rows:
                    break
                all_rows.extend(rows)
                print(f"  coletado: termo='{term}' cidade='{city}' pág={page} (+{len(rows)})")
                page += 1
                time.sleep(SLEEP_SECONDS)
                # Proteção simples contra paginação infinita.
                if page > 20:
                    break
    return all_rows


def save(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Salvo: {path} ({len(rows)} registros)")


if __name__ == "__main__":
    print("Iniciando coleta EURES...")
    rows = collect()
    save(rows, OUTPUT_PATH)
