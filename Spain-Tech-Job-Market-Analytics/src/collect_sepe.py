"""
collect_sepe.py
----------------
Coleta anúncios de vagas do portal Empléate/SEPE (https://www.sepe.es/)
para profissionais de Dados e Engenharia de Software na Espanha.

IMPORTANTE — LIMITAÇÃO DE AMBIENTE:
Assim como em collect_eures.py, este script não foi executado dentro do
ambiente de geração deste projeto (rede restrita). O dataset de
demonstração em data/raw/ foi gerado sinteticamente com o mesmo schema.
Rode `python src/collect_sepe.py` em uma máquina com acesso à internet
para realizar a coleta real.

O SEPE/Empléate não disponibiliza uma API pública de vagas; a coleta real
depende de parsing de HTML (BeautifulSoup) da listagem pública de ofertas
ou do uso do portal Empléate. Ajuste os seletores CSS abaixo após inspecionar
a página atual, pois o HTML muda com frequência.

Uso responsável:
- Respeite o robots.txt e os Termos de Uso do SEPE.
- Um único worker, com SLEEP_SECONDS entre requisições.
- Registre a URL de origem e a data de coleta de cada anúncio.
"""

import csv
import datetime as dt
import time
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.sepe.es"
SEARCH_PATH = "/HomeSepe/empleate/buscar-empleo.html"  # ajustar conforme estrutura vigente do site
SLEEP_SECONDS = 2.0
TIMEOUT = 20
HEADERS = {
    "User-Agent": "Spain-Tech-Job-Market-Analytics/1.0 (uso academico; contato: substitua-por-seu-email)"
}

SEARCH_TERMS = [
    "analista de datos",
    "ingeniero de datos",
    "cientifico de datos",
    "ingeniero de software",
    "desarrollador backend",
    "desarrollador frontend",
    "ingeniero devops",
    "ingeniero qa",
    "machine learning",
]

TARGET_CITIES = ["Madrid", "Barcelona", "Valencia", "Malaga", "A Coruna"]

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "sepe_raw.csv"

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


def fetch_listing_page(term: str, city: str, page: int) -> str | None:
    params = {"q": term, "loc": city, "page": page}
    try:
        resp = requests.get(BASE_URL + SEARCH_PATH, params=params, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        print(f"[AVISO] Falha ao buscar '{term}' em '{city}' (pág {page}): {exc}", file=sys.stderr)
        return None


def parse_listing(html: str) -> list[dict]:
    """Extrai vagas de uma página de listagem.

    Os seletores CSS abaixo são ilustrativos — inspecione o HTML real do
    portal (DevTools) e atualize as classes/ids antes de rodar em produção.
    """
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select("div.oferta-card"):  # ajustar seletor real
        title_el = card.select_one(".oferta-titulo")
        company_el = card.select_one(".oferta-empresa")
        city_el = card.select_one(".oferta-ciudad")
        link_el = card.select_one("a")
        salary_el = card.select_one(".oferta-salario")
        date_el = card.select_one(".oferta-fecha")

        rows.append({
            "source": "SEPE",
            "source_url": (BASE_URL + link_el["href"]) if link_el and link_el.has_attr("href") else "",
            "job_title": title_el.get_text(strip=True) if title_el else "",
            "company": company_el.get_text(strip=True) if company_el else "",
            "city": city_el.get_text(strip=True) if city_el else "",
            "region": "",
            "technologies_raw": "",  # normalmente exige abrir a página de detalhe da vaga
            "experience_raw": "",
            "work_mode_raw": "",
            "salary_raw": salary_el.get_text(strip=True) if salary_el else "",
            "posted_date": date_el.get_text(strip=True) if date_el else "",
            "collected_date": dt.date.today().isoformat(),
        })
    return rows


def collect() -> list[dict]:
    all_rows: list[dict] = []
    for term in SEARCH_TERMS:
        for city in TARGET_CITIES:
            page = 0
            while True:
                html = fetch_listing_page(term, city, page)
                if not html:
                    break
                rows = parse_listing(html)
                if not rows:
                    break
                all_rows.extend(rows)
                print(f"  coletado: termo='{term}' cidade='{city}' pág={page} (+{len(rows)})")
                page += 1
                time.sleep(SLEEP_SECONDS)
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
    print("Iniciando coleta SEPE...")
    rows = collect()
    save(rows, OUTPUT_PATH)
