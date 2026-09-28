# Dicionário de Variáveis — Spain-Tech-Job-Market-Analytics

## `data/raw/*.csv` (saída bruta da coleta)

| Campo               | Tipo   | Descrição                                                            |
|---------------------|--------|-----------------------------------------------------------------------|
| source               | texto  | Origem do anúncio: `EURES` ou `SEPE`.                                 |
| source_url           | texto  | URL do anúncio original (rastreabilidade).                            |
| job_title            | texto  | Título do cargo, como publicado (sem padronização).                   |
| company              | texto  | Nome da empresa contratante.                                          |
| city                 | texto  | Cidade da vaga, como publicada.                                       |
| region               | texto  | Comunidade autónoma, como publicada.                                  |
| technologies_raw     | texto  | Tecnologias/competências mencionadas, separadas por vírgula/`;`/`/`.  |
| experience_raw       | texto  | Nível de experiência exigido, como publicado.                         |
| work_mode_raw        | texto  | Modalidade de trabalho, como publicada (presencial/híbrido/remoto).   |
| salary_raw           | texto  | Faixa salarial, como publicada (pode estar vazio).                    |
| posted_date          | data   | Data de publicação do anúncio (AAAA-MM-DD).                           |
| collected_date       | data   | Data em que o anúncio foi coletado (AAAA-MM-DD).                      |

## `data/processed/job_postings_clean.csv` (uma linha por vaga, após limpeza)

| Campo                     | Tipo    | Descrição                                                                 |
|---------------------------|---------|------------------------------------------------------------------------------|
| posting_id                | inteiro | Identificador único da vaga após deduplicação.                              |
| source                    | texto   | `EURES` ou `SEPE`.                                                           |
| source_url                | texto   | URL original.                                                                |
| job_title                 | texto   | Título original (não padronizado).                                          |
| job_title_standardized    | texto   | Cargo padronizado (ex.: `Data Analyst`, `Backend Developer`).               |
| professional_area         | texto   | `Dados` ou `Engenharia de Software`.                                        |
| company                   | texto   | Empresa contratante.                                                         |
| city                      | texto   | Cidade padronizada.                                                          |
| region                    | texto   | Comunidade autónoma.                                                         |
| experience_level          | texto   | Nível de experiência (padronizado quando possível).                         |
| work_mode                 | texto   | `Presencial`, `Híbrido`, `Remoto` ou `Não informado`.                        |
| salary_min                | inteiro | Limite inferior da faixa salarial (EUR/ano), se divulgado.                  |
| salary_max                | inteiro | Limite superior da faixa salarial (EUR/ano), se divulgado.                  |
| salary_disclosed          | booleano| `1` se o anúncio divulga salário; `0` caso contrário.                       |
| posted_date               | data    | Data de publicação.                                                          |
| collected_date            | data    | Data de coleta.                                                              |

## `data/processed/job_skills_long.csv` (formato longo: 1 linha por vaga × competência)

| Campo       | Tipo    | Descrição                                             |
|-------------|---------|--------------------------------------------------------|
| posting_id  | inteiro | Referência à vaga em `job_postings_clean.csv`.        |
| skill       | texto   | Nome padronizado da competência/tecnologia.           |

## Banco de dados `database/spain_tech_jobs.db`

Ver `sql/schema.sql` para a definição completa das tabelas `cities`,
`skills`, `postings` e `posting_skills` (chaves primárias, estrangeiras e
índices).

## Notas de padronização

- **Cargos**: agrupados por expressões regulares em `src/clean_data.py`
  (`TITLE_STANDARDIZATION`). Cargos não reconhecidos ficam com o título
  original em formato `Title Case`.
- **Competências**: normalizadas via dicionário `SKILL_ALIASES` (ex.:
  `"powerbi"`, `"power bi"` → `Power BI`).
- **Salário**: extraído por regex de números com 4+ dígitos no texto
  bruto; assume-se moeda EUR e periodicidade anual, conforme padrão dos
  anúncios espanhóis. Anúncios sem números reconhecíveis são marcados
  como `salary_disclosed = 0`.
