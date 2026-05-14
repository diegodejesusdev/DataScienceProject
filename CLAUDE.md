# CLAUDE.md — Proyecto ConstruNorte

Este archivo le dice a Claude Code todo lo que necesita saber para trabajar en este proyecto sin equivocarse. **Lee este archivo completo antes de hacer cualquier cambio.**

---

## 1. Contexto del proyecto

**Título:** Análisis predictivo de la rotación de inventarios mediante machine learning aplicado a las ventas históricas de CONSTRUNORTE COMERCIALIZADORA S.A.S., periodo 2024–2025.

**Equipo:** Diego Andrés De Jesús Montenegro y Luis David Andrade Díaz.
**Institución:** Corporación Universitaria Comfacauca — Unicomfacauca.
**Programa:** Diplomado en Ingeniería y Ciencia de Datos Aplicada.
**Tutor:** Ing. Francisco Javier Obando.
**Plazo:** 4 semanas (entrega 28 de mayo de 2026).

**Problema de negocio:** ConstruNorte (comercializadora de materiales de construcción) tiene ~600.000 registros transaccionales de 2024-2025 pero no sabe qué productos rotan más, ni puede anticipar la demanda futura. Esto provoca quiebres de stock en productos importantes y sobreinventario en productos lentos.

**Objetivo general:** Desarrollar un sistema analítico predictivo basado en machine learning que pronostique la demanda y caracterice la rotación de productos comercializados por ConstruNorte, mediante el análisis de sus datos transaccionales del periodo enero 2024 – diciembre 2025.

**Objetivos específicos:**
- **OE1.** Comprender el contexto comercial, logístico e identificar fuentes y patrones iniciales mediante un EDA.
- **OE2.** Preparar los datos (limpieza, depuración, transformación, construcción de variables).
- **OE3.** Construir modelos de machine learning para pronóstico de demanda, evaluando su desempeño.
- **OE4.** Evaluar resultados y patrones de rotación mediante indicadores, tablas y visualizaciones que orienten la organización de bodega.

**Tipo de análisis:** Predictivo (forecasting de demanda) con apoyo descriptivo (clasificación ABC/XYZ).

---

## 2. Stack tecnológico (FIJO — no cambiar sin discutirlo)

| Capa | Herramienta | Dónde corre |
|---|---|---|
| Contenedorización | Docker + Docker Compose | Host (Mac) |
| Base de datos | MySQL 8.0 | Contenedor `construnorte_mysql` |
| Admin BD (GUI web) | Adminer | Contenedor `construnorte_adminer` |
| Ambiente análisis | Jupyter Lab + Python 3.11 | Contenedor `construnorte_jupyter` |
| ETL visual | Apache Hop | **Nativo en Mac** (la GUI no se contenedoriza) |
| Dashboard | Tableau Desktop (licencia académica) | **Nativo en Mac** |
| Control de versiones | Git + GitHub | Host |

**Librerías Python clave:** pandas, numpy, sqlalchemy, pymysql, scikit-learn, lightgbm, xgboost, prophet, matplotlib, seaborn, plotly, holidays.

**Modelos ML que se entrenarán y compararán:**
1. **Baseline simple** (media móvil 4 semanas) — siempre primero, sirve de piso.
2. **LightGBM Regressor** — modelo principal global con SKU como feature categórica.
3. **XGBoost Regressor** — modelo de comparación con misma estrategia que LightGBM.
4. **Prophet** — modelo de comparación para SKUs individuales del top.

---

## 3. Estructura del repositorio

```
construnorte-rotacion/
├── CLAUDE.md                       # Este archivo (contexto del proyecto)
├── README.md                       # Instrucciones públicas de instalación y uso
├── .claude/
│   └── skills/                     # Skills especializadas (lee la relevante antes de cada tarea)
│       ├── etl-pipeline/
│       ├── feature-engineering/
│       ├── abc-xyz-classification/
│       ├── time-series-modeling/
│       ├── evaluation-metrics/
│       ├── mysql-operations/
│       ├── notebook-style/
│       └── project-conventions/
├── docker-compose.yml              # Orquestación de los 3 servicios
├── .env                            # (gitignored) credenciales locales
├── .env.example                    # plantilla pública sin contraseñas
├── .gitignore
├── docker/
│   └── jupyter/
│       ├── Dockerfile              # Imagen custom para Jupyter
│       └── requirements.txt        # Librerías Python en el contenedor
├── db/
│   └── init/
│       └── 01_schema.sql           # Schema inicial de MySQL (autoejecutado)
├── data/
│   ├── raw/                        # CSV original (NO subir a Git)
│   └── processed/                  # Datasets intermedios (NO subir a Git)
├── notebooks/
│   ├── 01_perfil_inicial.ipynb     # Comprensión de datos
│   ├── 02_eda.ipynb                # Análisis exploratorio
│   ├── 03_preparacion.ipynb        # Limpieza y feature engineering
│   ├── 04_abc_xyz.ipynb            # Clasificación ABC/XYZ
│   ├── 05_baseline.ipynb           # Modelo baseline
│   ├── 06_lightgbm.ipynb           # LightGBM
│   ├── 07_xgboost.ipynb            # XGBoost
│   ├── 08_prophet.ipynb            # Prophet
│   └── 09_evaluacion_final.ipynb   # Comparación de modelos
├── src/
│   ├── __init__.py
│   ├── db.py                       # Conexión a MySQL (engine SQLAlchemy)
│   ├── etl.py                      # Pipeline ETL programático
│   ├── features.py                 # Feature engineering reutilizable
│   ├── abc_xyz.py                  # Clasificación ABC/XYZ
│   ├── models.py                   # Entrenamiento de modelos
│   └── evaluation.py               # Cálculo de métricas MAE/RMSE/MAPE
├── hop/
│   └── etl_construnorte.hpl        # Flujo visual de Apache Hop
├── reports/
│   ├── informe_ejecutivo.docx
│   └── figures/
├── dashboard/
│   └── construnorte_rotacion.twb   # Tableau workbook
└── docs/
    ├── 01_comprension_negocio.md
    ├── 02_diccionario_datos.md
    ├── 03_preparacion_datos.md
    ├── 04_modelado.md
    └── 05_decisiones_tecnicas.md
```

---

## 4. Dataset

**Fuente:** CSV transaccional de ConstruNorte (~600K filas, 33 columnas, periodo 2024-01 a 2025-12+).

**Granularidad de la fila cruda:** una línea de remisión/venta por SKU.

**Variables que se RETIENEN (variables de producto y transacción):**
- `Fecha`, `Item`, `Nombre Item`, `Referencia Item`, `Codigo Barra Item`
- `Unidad Inventario 1 Item`, `Proveedor Codigo Item`, `Proveedor Nombre Item`
- `Nombre Linea N1`, `Nombre Linea N2`, `Centro de Operacion`, `Tipo de Documento`
- `Cantidad 1`, `Precio Uni`, `Valor Bruto`, `Valor Costo`, `Peso`

**Variables que se ELIMINAN (datos personales — Ley 1581 de 2012):**
- `Cliente`, `Nombre Cliente`, `Direccion Cliente`, `Nit Cliente`
- `Ciudad Cliente`, `Ciudad Descripcion Cliente`, `Nombre Criterio Cliente 1`
- `Vendedor`, `Nombre Vendedor`, `Cedula Vendedor`
- `Documento Remision`, `Documento Ventas`, `Documento Pedido`

**Esto debe hacerse en la FASE DE PREPARACIÓN antes de almacenar el dataset modelable en MySQL.**

---

## 5. Convenciones de código

### Python
- **Estilo:** PEP 8.
- **Encoding:** UTF-8 siempre.
- **Type hints** en todas las funciones públicas.
- **Docstrings** en formato Google style.
- **Variables y funciones** en `snake_case`, en español cuando se refieran al dominio (`cantidad`, `valor_bruto`) y en inglés cuando sean técnicas (`train`, `predict`).
- **Constantes** en `UPPER_SNAKE_CASE`.
- **Imports** ordenados: stdlib → third-party → local.
- **NO usar `print()`** en módulos `src/`. Usar `logging`.
- En notebooks, `print()` está bien para explorar.

### SQL
- **Nombres de tablas y columnas** en `snake_case`, en español para el dominio.
- **Llaves primarias** se llaman `id`.
- **Llaves foráneas** se llaman `<tabla>_id`.
- **Fechas** como `DATE`, **timestamps** como `TIMESTAMP`.
- Toda tabla tiene `created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.

### Notebooks
- Cada notebook empieza con una celda Markdown que incluye: objetivo, inputs, outputs y autor.
- Primera celda de código: imports.
- Segunda celda: configuración (rutas, conexión BD).
- **Lee la skill `notebook-style/` antes de crear o editar notebooks.**

### Git
- **Commits** en español, en imperativo: "feat: agregar limpieza de outliers".
- **Prefijos:** `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, `wip:`.
- **NO commitear** archivos en `data/raw/`, `data/processed/`, `models/*.pkl`, `.env`.
- **NO commitear** notebooks con outputs pesados. Usar `nbstripout` o limpiar antes.

---

## 6. Comandos esenciales

### Docker
```bash
docker compose up -d              # Levantar los 3 servicios
docker compose down               # Apagar (mantiene datos)
docker compose down -v            # Apagar y BORRAR datos (cuidado)
docker compose ps                 # Ver estado
docker compose logs -f mysql      # Ver logs de un servicio
docker compose build jupyter      # Rebuild si cambia el Dockerfile
```

### MySQL
```bash
# Entrar al cliente mysql del contenedor
docker exec -it construnorte_mysql mysql -u construnorte_user -p construnorte

# Backup
docker exec construnorte_mysql mysqldump -u root -p construnorte > backup.sql
```

### Jupyter
- Abrir en navegador: `http://localhost:8888/?token=construnorte2026`
- Adminer: `http://localhost:8080` (host: `mysql`, no `localhost`)

### Python (desde host nativo, si se necesita)
```bash
python -m venv venv
source venv/bin/activate
pip install -r docker/jupyter/requirements.txt
```

---

## 7. Reglas que Claude Code debe seguir SIEMPRE

1. **NUNCA hagas split aleatorio de los datos.** Es serie de tiempo — siempre usar `TimeSeriesSplit` de sklearn o partición temporal manual. Hacer split aleatorio filtra el futuro al modelo y es una violación grave de la metodología.

2. **NUNCA pongas credenciales en el código.** Todo va en `.env` y se lee con `python-dotenv` u `os.getenv()`.

3. **NUNCA subas el dataset original a Git.** `data/raw/` y `data/processed/` están en `.gitignore`. Si necesitas compartir una muestra, genera un CSV con `df.sample(1000)` y guárdalo en `data/sample/` con extensión explícita.

4. **NUNCA proceses los datos personales.** Antes de cualquier análisis, los `df.drop()` correspondientes deben ejecutarse. Si la variable está en la lista de "ELIMINAR" arriba, no debe llegar a MySQL.

5. **SIEMPRE agrega los datos a granularidad SEMANAL por SKU antes de modelar.** La fila cruda es transaccional; la fila de modelado es `(item, año, semana, centro_operacion) → cantidad_total`.

6. **SIEMPRE reporta MAE, RMSE y MAPE juntos.** Nunca solo una. Si la variable real tiene ceros, advierte que MAPE puede explotar y usa sMAPE como alternativa.

7. **SIEMPRE compara contra el baseline** (media móvil de 4 semanas). Si el modelo no le gana al baseline, no sirve.

8. **SIEMPRE lee la skill relevante antes de empezar una tarea nueva.** Las skills están en `.claude/skills/`. Sus nombres son autoexplicativos.

9. **NO instales librerías nuevas** sin actualizar `docker/jupyter/requirements.txt`. Si añades algo, agrégalo al archivo y avisa que hay que hacer `docker compose build jupyter`.

10. **NO cambies el `docker-compose.yml`** sin discutirlo. Si propones cambios, hazlos en una rama nueva o como sugerencia en texto.

---

## 8. Skills disponibles

Antes de empezar cualquier tarea técnica, **lee la skill correspondiente**. Cada skill vive en `.claude/skills/<nombre>/SKILL.md`.

| Skill | Cuándo leerla |
|---|---|
| `project-conventions/` | Antes de crear cualquier archivo nuevo |
| `mysql-operations/` | Antes de tocar tablas, hacer queries o cargar datos |
| `etl-pipeline/` | Antes de procesar/limpiar el CSV o cargar a MySQL |
| `feature-engineering/` | Antes de generar features (lags, calendario, medias móviles) |
| `abc-xyz-classification/` | Antes de calcular ABC, XYZ o la matriz combinada |
| `time-series-modeling/` | Antes de entrenar LightGBM, XGBoost o Prophet |
| `evaluation-metrics/` | Antes de calcular o reportar MAE/RMSE/MAPE |
| `notebook-style/` | Antes de crear o modificar un notebook |

---

## 9. Información de privacidad y seguridad

- El dataset contiene **datos personales** protegidos por la Ley 1581 de 2012 de Colombia.
- El equipo tiene **carta de autorización firmada** por ConstruNorte.
- Los archivos crudos viven solo en los equipos del equipo, protegidos por contraseña.
- Al cierre del proyecto, los `.csv` originales se eliminan.
- El repositorio público en GitHub **NUNCA** contiene el dataset original.
- En el informe, los nombres de productos y proveedores pueden anonimizarse si la dirección de ConstruNorte lo solicita.

---

## 10. Cómo trabajar con Claude Code en este proyecto

**Flujo recomendado:**

1. Abre Claude Code en la raíz del proyecto.
2. Cuando inicies sesión, Claude lee este `CLAUDE.md` automáticamente.
3. Para una tarea nueva, indica explícitamente: *"Lee primero la skill `<nombre>` antes de empezar."*
4. Pide que use **commits atómicos** (un cambio lógico por commit).
5. Pide que **valide en MySQL** después de cargar datos (con un `SELECT COUNT(*)`).
6. Si Claude propone instalar una librería nueva, recuerda actualizar `requirements.txt` y hacer rebuild.

**Frase útil para iniciar sesiones:**
> *"Voy a trabajar en [TAREA]. Lee primero `CLAUDE.md` y la skill `<nombre>/SKILL.md`, luego propón un plan en 5 pasos antes de empezar a escribir código."*
