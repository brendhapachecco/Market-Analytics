# Informe Técnico

## Spain-Tech-Job-Market-Analytics

**Pregunta de investigación:** ¿Cómo varían las competencias técnicas exigidas
para profesionales de Datos e Ingeniería de Software entre diferentes
regiones de España?

---

## 1. Introducción

Este proyecto analiza anuncios de empleo publicados en portales públicos
españoles (EURES y SEPE/Empléate) para comparar las competencias técnicas
solicitadas a profesionales de **Datos** (Data Analyst, Data Engineer,
Data Scientist, BI Analyst, Machine Learning Engineer) e **Ingeniería de
Software** (Software Engineer, Backend/Frontend/Full Stack Developer,
DevOps Engineer, QA Engineer) en cinco ciudades: Madrid, Barcelona,
Valencia, Málaga y A Coruña.

## 2. Metodología

### 2.1 Recolección de datos

Se desarrollaron dos recolectores (`src/collect_eures.py` y
`src/collect_sepe.py`) que consultan, respectivamente, el motor de
búsqueda del portal EURES y el portal público de ofertas del SEPE,
filtrando por los términos de búsqueda relacionados con las dos áreas
profesionales de interés y por las cinco ciudades objetivo.

> **Nota metodológica importante:** el entorno en el que se construyó
> este proyecto no tuvo acceso de red a `eures.europa.eu` ni a
> `www.sepe.es`. Por lo tanto, **los datos incluidos en `data/raw/` son
> sintéticos**, generados por `src/generate_sample_data.py` con la misma
> estructura (schema) que produciría una recolección real, para permitir
> demostrar de forma completa y funcional todo el pipeline (limpieza,
> base de datos SQL y dashboard). Antes de cualquier uso analítico real,
> es imprescindible ejecutar los recolectores reales en una máquina con
> acceso a internet y sustituir los archivos de `data/raw/`.

### 2.2 Construcción de la base

Cada anuncio recolectado se registra con: cargo, ciudad, empresa,
tecnologías exigidas, experiencia, modalidad de trabajo, salario
informado (cuando existe) y fecha de publicación, además del origen
(EURES o SEPE) y la fecha de recolección, para trazabilidad.

### 2.3 Tratamiento de los datos

El script `src/clean_data.py` realiza:

- **Estandarización de cargos**: variantes en español e inglés (p. ej.
  "Analista de Datos" / "Data Analyst") se agrupan en una categoría
  única (`job_title_standardized`).
- **Estandarización de competencias**: alias de la misma tecnología
  (p. ej. "powerbi", "power bi") se normalizan a un solo nombre.
- **Detección de duplicados**: anuncios con la misma empresa, cargo
  estandarizado, ciudad y fecha de publicación se consideran el mismo
  anuncio republicado y se eliminan, conservando la primera ocurrencia.
- **Tratamiento de salarios no divulgados**: cuando el anuncio no
  informa salario, los campos `salary_min`/`salary_max` quedan nulos y
  `salary_disclosed = 0`, en lugar de imputar un valor. Esto preserva la
  distinción entre "no hay dato" y "salario bajo".

### 2.4 Modelo de datos y análisis

Los datos limpios se cargan en una base SQLite (`database/spain_tech_jobs.db`)
con un esquema en estrella (`sql/schema.sql`): una tabla de hechos
`postings`, una dimensión `cities` y una dimensión `skills` conectada por
la tabla puente `posting_skills` (relación N:N, ya que un anuncio puede
exigir varias tecnologías). Las consultas analíticas de referencia están
documentadas en `sql/analytical_queries.sql`.

### 2.5 Visualización

El dashboard (`dashboard/app.py`, construido con Streamlit y Plotly)
permite filtrar por ciudad, cargo, área profesional, modalidad de
trabajo y tecnología, mostrando: mapa de calor de tecnologías por
ciudad, ranking de tecnologías por área, distribución de modalidad de
trabajo por ciudad y una tabla detallada de anuncios.

## 3. Resultados (dataset de demostración)

Los siguientes resultados se calcularon sobre el dataset sintético de
617 anuncios incluido en el repositorio, **únicamente para validar el
pipeline** — no deben interpretarse como una caracterización real del
mercado laboral español.

- Distribución de anuncios por ciudad: Madrid (248), Barcelona (179),
  Valencia (82), Málaga (64) y A Coruña (44) — reflejando el peso
  relativo que suele observarse en la concentración de empleo tech en
  Madrid y Barcelona.
- Proporción de anuncios con salario divulgado por ciudad: entre 69,3%
  (Barcelona) y 79,5% (A Coruña).
- Tecnologías más frecuentes en el área de **Datos**: R, AWS, dbt, SQL y
  Snowflake. En **Ingeniería de Software**: Azure, Java, Angular, Git y
  Docker.
- Al comparar Python, SQL, Power BI y Java entre comunidades autónomas,
  Madrid y Cataluña concentran el mayor número absoluto de menciones de
  las cuatro tecnologías, lo cual es consistente con su mayor volumen
  total de anuncios (y no necesariamente con una mayor intensidad
  relativa por vaga; para eso, comparar porcentajes normalizados por el
  total de anuncios de cada región, no solo el conteo absoluto).
- La modalidad de trabajo se distribuye de forma relativamente
  equilibrada entre Híbrido (222), Remoto (201) y Presencial (194) en el
  dataset de demostración.

*(Al sustituir los datos sintéticos por una recolección real, esta
sección debe reescribirse íntegramente con los resultados obtenidos.)*

## 4. Limitaciones y representatividad de la muestra

Este es el punto que el equipo evaluador señaló como diferencial
académico central del proyecto, y se abordan explícitamente los
siguientes puntos:

1. **Cobertura parcial de fuentes.** EURES y SEPE no agregan la
   totalidad de las vacantes publicadas en España; portales privados
   (LinkedIn, InfoJobs, Glassdoor, sitios propios de empresas) también
   concentran una parte relevante — probablemente mayoritaria en el
   sector tecnológico — de las ofertas. Los resultados de este estudio
   describen **el subconjunto de vacantes públicas visibles en EURES y
   SEPE**, no "el mercado laboral tecnológico español" en su totalidad.
2. **Sesgo de tipo de empleador.** Portales públicos de empleo tienden a
   sobre-representar administración pública, grandes empresas y
   procesos formales de contratación, y a sub-representar startups y
   contrataciones por referencia o headhunting directo.
3. **Mención vs. exigencia real de una competencia.** Que una tecnología
   aparezca en el texto de un anuncio no garantiza que sea un requisito
   excluyente; puede figurar como "deseable", como parte de una lista
   genérica de tecnologías de la empresa, o incluso copiada de una
   plantilla de anuncio anterior. Este proyecto **cuenta menciones
   textuales**, no exigencias verificadas caso por caso; se recomienda
   leer los porcentajes como "frecuencia de mención", no como
   "porcentaje de vacantes que exigen estrictamente X".
4. **Anuncios sin salario informado.** Entre el 20% y el 30% de los
   anuncios (según la ciudad, en el dataset de demostración) no informa
   salario. Excluir estos registros del cálculo de salario promedio
   introduce un sesgo si la decisión de no publicar el salario está
   correlacionada con el nivel salarial (p. ej., empresas que pagan
   menos podrían omitir el dato con más frecuencia). Los promedios
   salariales reportados deben leerse como "promedio entre quienes
   divulgan", no como representativos de todas las vacantes.
5. **Volumen desigual entre ciudades.** Ciudades con menor volumen de
   anuncios (p. ej. A Coruña) generan estimaciones de frecuencia de
   tecnologías más inestables (mayor varianza muestral) que ciudades
   con mayor volumen (Madrid, Barcelona). Comparaciones entre ciudades
   con volúmenes muy distintos deben interpretarse con cautela,
   idealmente acompañadas de intervalos de confianza o del tamaño
   muestral explícito en cada gráfico.
6. **Ventana temporal acotada.** La recolección cubre un período
   definido (ver `collected_date` en los datos); tendencias
   estacionales del mercado laboral (p. ej. menor publicación de
   vacantes en agosto en España) pueden afectar la comparabilidad entre
   ciudades si la proporción de anuncios por mes difiere entre ellas.
7. **Dataset de demostración sintético.** Como se detalla en la sección
   2.1, los resultados de la sección 3 provienen de datos simulados y
   sirven solo para validar el funcionamiento técnico del pipeline.

## 5. Conclusión

El pipeline desarrollado —recolección, limpieza, modelado en SQL y
dashboard interactivo— permite responder de forma reproducible a la
pregunta de investigación una vez que se disponga de una recolección
real de EURES y SEPE. La comparación de competencias entre regiones debe
presentarse siempre junto con el tamaño muestral y la proporción de
datos faltantes (particularmente el salario), y los resultados deben
enmarcarse explícitamente como un análisis de anuncios públicos
visibles, no del mercado laboral en su totalidad.

## 6. Próximos pasos sugeridos

- Ejecutar `src/collect_eures.py` y `src/collect_sepe.py` en un entorno
  con acceso a internet y validar/ajustar los selectores y parámetros de
  la API/HTML, que pueden haber cambiado desde la redacción de este
  informe.
- Ampliar la ventana temporal de recolección para reducir el efecto de
  estacionalidad.
- Normalizar las frecuencias de tecnología por el total de anuncios de
  cada ciudad/región (porcentaje), además del conteo absoluto, en todos
  los gráficos comparativos.
- Considerar fuentes adicionales (con permisos de reutilización claros)
  para reducir el sesgo de cobertura de portales públicos.
