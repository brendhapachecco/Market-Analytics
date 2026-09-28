# Spain-Tech-Job-Market-Analytics

**Pergunta de investigação:** Como variam as competências técnicas
exigidas para profissionais de Dados e Engenharia de Software entre
diferentes regiões da Espanha?

Este projeto coleta anúncios de vagas de fontes públicas espanholas
(EURES e SEPE), constrói uma base estruturada, trata e padroniza os
dados, carrega-os em um banco SQL e disponibiliza um dashboard
interativo para comparar competências técnicas por cidade, cargo e
modalidade de trabalho.

> ⚠️ **Aviso importante sobre os dados incluídos neste repositório:**
> os coletores (`src/collect_eures.py` e `src/collect_sepe.py`) foram
> desenvolvidos para uso real, mas **não foram executados contra a
> internet** durante a geração deste repositório (o ambiente de
> desenvolvimento tinha acesso de rede restrito). Por isso, o arquivo em
> `data/raw/sample_postings_raw.csv` é **sintético** (gerado por
> `src/generate_sample_data.py`), com a mesma estrutura que a coleta
> real produziria, apenas para que todo o pipeline (limpeza → banco SQL
> → dashboard) possa ser demonstrado de ponta a ponta. Veja a seção
> [Executando a coleta real](#executando-a-coleta-real) para substituir
> pelos dados reais.

## Estrutura do repositório

```
Spain-Tech-Job-Market-Analytics/
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                       # dados brutos (coleta real ou sintética)
│   ├── processed/                 # dados limpos e padronizados
│   └── data_dictionary.md         # dicionário de variáveis
├── src/
│   ├── collect_eures.py           # coletor real — portal EURES
│   ├── collect_sepe.py            # coletor real — portal SEPE/Empléate
│   ├── generate_sample_data.py    # gera dataset sintético de demonstração
│   ├── clean_data.py              # limpeza, padronização, deduplicação
│   └── build_database.py          # carrega os dados no banco SQLite
├── sql/
│   ├── schema.sql                 # schema do banco (estrela)
│   └── analytical_queries.sql     # consultas analíticas de referência
├── database/
│   └── spain_tech_jobs.db         # banco SQLite gerado (incluso, pronto p/ uso)
├── dashboard/
│   └── app.py                     # dashboard interativo (Streamlit)
└── reports/
    └── informe_tecnico.md         # relatório técnico em espanhol
```

## Instalação

Requer Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Como executar o pipeline completo

O banco `database/spain_tech_jobs.db` já vem pronto no repositório
(construído a partir do dataset sintético), então você pode ir direto
para o [dashboard](#rodando-o-dashboard). Para reconstruir tudo do zero:

```bash
# 1) Gerar dados (sintéticos, para demonstração) OU rodar a coleta real (ver abaixo)
python src/generate_sample_data.py

# 2) Tratar/padronizar os dados
python src/clean_data.py

# 3) Construir o banco SQLite
python src/build_database.py
```

## Executando a coleta real

Os coletores reais dependem de acesso à internet e devem ser
executados fora deste ambiente de geração do projeto:

```bash
python src/collect_eures.py   # gera data/raw/eures_raw.csv
python src/collect_sepe.py    # gera data/raw/sepe_raw.csv
```

Antes de rodar em produção:

- Inspecione a resposta real da API do EURES e o HTML atual do portal
  SEPE/Empléate — ambos os scripts documentam, em comentários, quais
  pontos (parâmetros de busca, seletores CSS) provavelmente precisarão
  de ajuste, pois esses portais mudam sua estrutura com frequência.
- Respeite os Termos de Uso e o `robots.txt` de cada portal.
- Depois de rodar os coletores reais, **apague ou mova**
  `data/raw/sample_postings_raw.csv` antes de rodar `clean_data.py`,
  para que a análise não misture dados sintéticos com dados reais.
- Repita os passos 2 e 3 acima (`clean_data.py` e `build_database.py`)
  para reconstruir o banco com os dados reais.

## Rodando o dashboard

```bash
streamlit run dashboard/app.py
```

O dashboard abre no navegador (por padrão em `http://localhost:8501`) e
permite filtrar por cidade, área profissional, cargo, modalidade de
trabalho e tecnologia, exibindo:

- Mapa de calor de frequência de tecnologias por cidade.
- Ranking das tecnologias mais exigidas na seleção atual.
- Distribuição de vagas por cidade e por modalidade de trabalho.
- Tabela detalhada das vagas filtradas.

## Consultando o banco SQL diretamente

```bash
sqlite3 database/spain_tech_jobs.db
.read sql/analytical_queries.sql
```

Ou, em Python:

```python
import sqlite3, pandas as pd
conn = sqlite3.connect("database/spain_tech_jobs.db")
df = pd.read_sql_query("SELECT * FROM postings LIMIT 10", conn)
```

## Atualizando os dados periodicamente

Para atualizar a base com novas coletas:

1. Rode `collect_eures.py` e `collect_sepe.py` novamente (idealmente em
   um agendador — cron, GitHub Actions, etc.).
2. Junte os novos arquivos aos já existentes em `data/raw/` (ou
   substitua, se preferir apenas o período mais recente).
3. Rode `clean_data.py` e `build_database.py` novamente — a
   deduplicação evita contar duas vezes o mesmo anúncio republicado.

## Limitações da amostra

Este projeto documenta explicitamente que os anúncios coletados via
EURES e SEPE **não representam a totalidade das vagas existentes na
Espanha**, e que "tecnologia mencionada no anúncio" não é sinônimo de
"competência efetivamente exigida". Veja a discussão completa em
[`reports/informe_tecnico.md`](reports/informe_tecnico.md), seção
"Limitaciones y representatividad de la muestra".

## Dicionário de variáveis

Ver [`data/data_dictionary.md`](data/data_dictionary.md).

## Licença

Este projeto está licenciado sob a licença MIT — veja [`LICENSE`](LICENSE).
