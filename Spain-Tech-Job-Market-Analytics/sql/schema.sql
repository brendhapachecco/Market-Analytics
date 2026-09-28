-- ============================================================================
-- schema.sql
-- Spain-Tech-Job-Market-Analytics
-- Modelo relacional simples (esquema estrela) para anúncios de vagas de
-- Dados e Engenharia de Software na Espanha.
-- Compatível com SQLite (usado por src/build_database.py) e facilmente
-- portável para PostgreSQL/MySQL com pequenos ajustes de tipos.
-- ============================================================================

DROP TABLE IF EXISTS posting_skills;
DROP TABLE IF EXISTS postings;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS cities;

-- Dimensão: cidades e sua região/comunidade autónoma
CREATE TABLE cities (
    city_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    city_name   TEXT NOT NULL UNIQUE,
    region      TEXT NOT NULL
);

-- Dimensão: competências técnicas mencionadas nos anúncios
CREATE TABLE skills (
    skill_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    skill_name  TEXT NOT NULL UNIQUE
);

-- Fato: um anúncio de vaga (após limpeza/deduplicação)
CREATE TABLE postings (
    posting_id              INTEGER PRIMARY KEY,
    source                  TEXT NOT NULL,             -- 'EURES' ou 'SEPE'
    source_url              TEXT,
    job_title_raw           TEXT,
    job_title_standardized  TEXT NOT NULL,
    professional_area       TEXT NOT NULL,             -- 'Dados' ou 'Engenharia de Software'
    company                 TEXT,
    city_id                 INTEGER REFERENCES cities(city_id),
    experience_level        TEXT,
    work_mode               TEXT,                      -- Presencial / Híbrido / Remoto / Não informado
    salary_min              INTEGER,
    salary_max              INTEGER,
    salary_disclosed        INTEGER NOT NULL CHECK (salary_disclosed IN (0, 1)),
    posted_date             DATE,
    collected_date          DATE
);

-- Ponte N:N entre vagas e competências
CREATE TABLE posting_skills (
    posting_id  INTEGER NOT NULL REFERENCES postings(posting_id),
    skill_id    INTEGER NOT NULL REFERENCES skills(skill_id),
    PRIMARY KEY (posting_id, skill_id)
);

CREATE INDEX idx_postings_city ON postings(city_id);
CREATE INDEX idx_postings_area ON postings(professional_area);
CREATE INDEX idx_postings_title ON postings(job_title_standardized);
CREATE INDEX idx_posting_skills_skill ON posting_skills(skill_id);
