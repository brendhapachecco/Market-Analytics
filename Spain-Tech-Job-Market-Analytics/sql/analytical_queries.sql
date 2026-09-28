-- ============================================================================
-- analytical_queries.sql
-- Consultas de apoio à pergunta de investigação:
-- "Como variam as competências técnicas exigidas para profissionais de
--  dados e Engenharia de Software entre diferentes regiões da Espanha?"
-- ============================================================================

-- 1) Frequência de cada tecnologia por cidade (tabela dinâmica manual)
SELECT
    c.city_name,
    s.skill_name,
    COUNT(*) AS n_mencoes,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY c.city_name), 1) AS pct_na_cidade
FROM posting_skills ps
JOIN postings p ON p.posting_id = ps.posting_id
JOIN cities c ON c.city_id = p.city_id
JOIN skills s ON s.skill_id = ps.skill_id
GROUP BY c.city_name, s.skill_name
ORDER BY c.city_name, n_mencoes DESC;

-- 2) Top 10 tecnologias mais exigidas, por área profissional
SELECT
    p.professional_area,
    s.skill_name,
    COUNT(*) AS n_mencoes
FROM posting_skills ps
JOIN postings p ON p.posting_id = ps.posting_id
JOIN skills s ON s.skill_id = ps.skill_id
GROUP BY p.professional_area, s.skill_name
ORDER BY p.professional_area, n_mencoes DESC;
-- (na aplicação/dashboard, limitar aos 10 primeiros por área)

-- 3) Comparação Python vs SQL vs Power BI vs Java entre regiões
SELECT
    c.region,
    s.skill_name,
    COUNT(*) AS n_mencoes
FROM posting_skills ps
JOIN postings p ON p.posting_id = ps.posting_id
JOIN cities c ON c.city_id = p.city_id
JOIN skills s ON s.skill_id = ps.skill_id
WHERE s.skill_name IN ('Python', 'SQL', 'Power BI', 'Java')
GROUP BY c.region, s.skill_name
ORDER BY c.region, s.skill_name;

-- 4) Cargos com maior número de anúncios, por cidade
SELECT
    c.city_name,
    p.job_title_standardized,
    COUNT(*) AS n_vagas
FROM postings p
JOIN cities c ON c.city_id = p.city_id
GROUP BY c.city_name, p.job_title_standardized
ORDER BY c.city_name, n_vagas DESC;

-- 5) Faixa salarial média (apenas anúncios com salário divulgado), por cidade e área
SELECT
    c.city_name,
    p.professional_area,
    COUNT(*) AS n_vagas_com_salario,
    ROUND(AVG(p.salary_min), 0) AS salario_min_medio,
    ROUND(AVG(p.salary_max), 0) AS salario_max_medio
FROM postings p
JOIN cities c ON c.city_id = p.city_id
WHERE p.salary_disclosed = 1
GROUP BY c.city_name, p.professional_area
ORDER BY c.city_name, p.professional_area;

-- 6) Proporção de vagas com salário divulgado, por cidade (indicador de
--    representatividade/transparência da amostra)
SELECT
    c.city_name,
    COUNT(*) AS total_vagas,
    SUM(p.salary_disclosed) AS vagas_com_salario,
    ROUND(100.0 * SUM(p.salary_disclosed) / COUNT(*), 1) AS pct_com_salario
FROM postings p
JOIN cities c ON c.city_id = p.city_id
GROUP BY c.city_name
ORDER BY pct_com_salario DESC;

-- 7) Distribuição de modalidade de trabalho (Presencial/Híbrido/Remoto), por cidade
SELECT
    c.city_name,
    p.work_mode,
    COUNT(*) AS n_vagas
FROM postings p
JOIN cities c ON c.city_id = p.city_id
GROUP BY c.city_name, p.work_mode
ORDER BY c.city_name, n_vagas DESC;

-- 8) Volume de anúncios coletados por fonte (EURES vs SEPE) e por mês
SELECT
    p.source,
    strftime('%Y-%m', p.posted_date) AS mes,
    COUNT(*) AS n_vagas
FROM postings p
GROUP BY p.source, mes
ORDER BY mes, p.source;
