"""
app.py — Dashboard Spain-Tech-Job-Market-Analytics
----------------------------------------------------
Dashboard interativo (Streamlit) para explorar como as competências
técnicas exigidas variam entre regiões da Espanha, para profissionais de
Dados e Engenharia de Software.

Como rodar:
    pip install -r requirements.txt
    streamlit run dashboard/app.py

Pré-requisito: o banco database/spain_tech_jobs.db deve existir. Se não
existir, rode antes:
    python src/generate_sample_data.py   # ou os coletores reais
    python src/clean_data.py
    python src/build_database.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "spain_tech_jobs.db"

st.set_page_config(page_title="Spain Tech Job Market Analytics", layout="wide")


@st.cache_data
def load_data():
    if not DB_PATH.exists():
        return None, None
    conn = sqlite3.connect(DB_PATH)
    postings = pd.read_sql_query(
        """
        SELECT p.posting_id, p.source, p.job_title_standardized, p.professional_area,
               p.company, c.city_name, c.region, p.experience_level, p.work_mode,
               p.salary_min, p.salary_max, p.salary_disclosed, p.posted_date
        FROM postings p
        JOIN cities c ON c.city_id = p.city_id
        """,
        conn,
    )
    skills = pd.read_sql_query(
        """
        SELECT ps.posting_id, s.skill_name
        FROM posting_skills ps
        JOIN skills s ON s.skill_id = ps.skill_id
        """,
        conn,
    )
    conn.close()
    return postings, skills


postings, skills = load_data()

st.title("🇪🇸 Spain Tech Job Market Analytics")
st.caption(
    "Como variam as competências técnicas exigidas para profissionais de Dados e "
    "Engenharia de Software entre diferentes regiões da Espanha?"
)

if postings is None:
    st.error(
        "Banco de dados não encontrado em `database/spain_tech_jobs.db`. "
        "Rode o pipeline primeiro: generate_sample_data.py → clean_data.py → build_database.py "
        "(veja o README.md)."
    )
    st.stop()

st.warning(
    "⚠️ Este dashboard está carregando um **dataset de demonstração sintético** "
    "(gerado por `src/generate_sample_data.py`), pois a coleta real via EURES/SEPE "
    "depende de acesso à internet no momento da execução. Substitua os dados em "
    "`data/raw/` pela saída real dos coletores para uma análise válida.",
    icon="⚠️",
)

# ---------------------------------------------------------------------------
# Filtros (barra lateral)
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

cities = sorted(postings["city_name"].unique())
areas = sorted(postings["professional_area"].unique())
titles = sorted(postings["job_title_standardized"].unique())
work_modes = sorted(postings["work_mode"].unique())
all_skills = sorted(skills["skill_name"].unique())

sel_cities = st.sidebar.multiselect("Cidade", cities, default=cities)
sel_areas = st.sidebar.multiselect("Área profissional", areas, default=areas)
sel_titles = st.sidebar.multiselect("Cargo", titles, default=titles)
sel_modes = st.sidebar.multiselect("Modalidade de trabalho", work_modes, default=work_modes)
sel_skills = st.sidebar.multiselect(
    "Tecnologia (filtra vagas que exigem QUALQUER uma das selecionadas)",
    all_skills,
    default=[],
)

filtered = postings[
    postings["city_name"].isin(sel_cities)
    & postings["professional_area"].isin(sel_areas)
    & postings["job_title_standardized"].isin(sel_titles)
    & postings["work_mode"].isin(sel_modes)
]

if sel_skills:
    posting_ids_with_skill = skills[skills["skill_name"].isin(sel_skills)]["posting_id"].unique()
    filtered = filtered[filtered["posting_id"].isin(posting_ids_with_skill)]

filtered_skills = skills[skills["posting_id"].isin(filtered["posting_id"])]

# ---------------------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Vagas (após filtro)", f"{len(filtered):,}".replace(",", "."))
col2.metric("Cidades cobertas", filtered["city_name"].nunique())
col3.metric(
    "% com salário divulgado",
    f"{100 * filtered['salary_disclosed'].mean():.0f}%" if len(filtered) else "—",
)
col4.metric("Competências distintas", filtered_skills["skill_name"].nunique())

st.divider()

# ---------------------------------------------------------------------------
# Gráfico 1: frequência de tecnologias por cidade (heatmap)
# ---------------------------------------------------------------------------
st.subheader("Frequência de tecnologias por cidade")
merged = filtered_skills.merge(filtered[["posting_id", "city_name"]], on="posting_id")
if len(merged):
    top_skills = merged["skill_name"].value_counts().head(15).index.tolist()
    pivot = (
        merged[merged["skill_name"].isin(top_skills)]
        .groupby(["city_name", "skill_name"])
        .size()
        .reset_index(name="mencoes")
    )
    fig_heat = px.density_heatmap(
        pivot, x="skill_name", y="city_name", z="mencoes",
        color_continuous_scale="Blues", text_auto=True,
    )
    fig_heat.update_layout(xaxis_title="Tecnologia", yaxis_title="Cidade", height=420)
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("Nenhum dado para os filtros selecionados.")

# ---------------------------------------------------------------------------
# Gráfico 2: top tecnologias por área profissional
# ---------------------------------------------------------------------------
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top tecnologias (área selecionada)")
    merged_area = filtered_skills.merge(
        filtered[["posting_id", "professional_area"]], on="posting_id"
    )
    if len(merged_area):
        top_n = (
            merged_area["skill_name"].value_counts().head(10).reset_index()
        )
        top_n.columns = ["skill_name", "mencoes"]
        fig_bar = px.bar(top_n, x="mencoes", y="skill_name", orientation="h")
        fig_bar.update_layout(yaxis={"categoryorder": "total ascending"}, height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

with col_b:
    st.subheader("Vagas por cidade")
    by_city = filtered["city_name"].value_counts().reset_index()
    by_city.columns = ["city_name", "n_vagas"]
    fig_city = px.bar(by_city, x="city_name", y="n_vagas")
    fig_city.update_layout(height=380)
    st.plotly_chart(fig_city, use_container_width=True)

# ---------------------------------------------------------------------------
# Gráfico 3: modalidade de trabalho por cidade
# ---------------------------------------------------------------------------
st.subheader("Modalidade de trabalho por cidade")
mode_city = filtered.groupby(["city_name", "work_mode"]).size().reset_index(name="n_vagas")
fig_mode = px.bar(mode_city, x="city_name", y="n_vagas", color="work_mode", barmode="stack")
st.plotly_chart(fig_mode, use_container_width=True)

# ---------------------------------------------------------------------------
# Tabela detalhada
# ---------------------------------------------------------------------------
st.subheader("Vagas (detalhe)")
st.dataframe(
    filtered[
        [
            "job_title_standardized", "professional_area", "company", "city_name",
            "region", "experience_level", "work_mode", "salary_min", "salary_max",
            "salary_disclosed", "posted_date", "source",
        ]
    ].sort_values("posted_date", ascending=False),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "Fonte: EURES e SEPE (ver README.md e reports/informe_tecnico.md para "
    "limitações de representatividade da amostra)."
)
