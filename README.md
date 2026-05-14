# ConstruNorte — Análisis Predictivo de Rotación de Inventarios

> Proyecto académico del **Diplomado en Ingeniería y Ciencia de Datos Aplicada** de la **Corporación Universitaria Comfacauca (Unicomfacauca)**.

Sistema analítico predictivo que pronostica la demanda y caracteriza la rotación de los productos comercializados por **CONSTRUNORTE COMERCIALIZADORA S.A.S.** durante el periodo enero 2024 – diciembre 2025, con el fin de respaldar decisiones de aprovisionamiento y organización de bodega.

---

## 👥 Equipo

- **Diego Andrés De Jesús Montenegro**
- **Luis David Andrade Díaz**
- **Tutor:** Ing. Francisco Javier Obando

---

## 🛠️ Stack tecnológico

| Capa | Herramienta | Dónde corre |
|---|---|---|
| Contenedorización | Docker + Docker Compose | Host |
| Base de datos | MySQL 8.0 | Contenedor |
| Admin BD (web) | Adminer | Contenedor |
| Análisis | Jupyter Lab + Python 3.11 | Contenedor |
| ETL visual | Apache Hop | Host |
| Modelado | LightGBM, XGBoost, Prophet | Contenedor |
| Dashboard | Tableau Desktop | Host |
| Versiones | Git + GitHub | Host |

---

## 🚀 Instalación y arranque

### Requisitos previos
- macOS, Linux o Windows con WSL2.
- **Docker Desktop** instalado y corriendo.
- **Git** instalado.
- (Opcional, nativo en Mac) Apache Hop y Tableau Desktop.

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/<usuario>/construnorte-rotacion.git
cd construnorte-rotacion
```

### Paso 2 — Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y reemplaza los valores `cambiar_*` por contraseñas reales.

### Paso 3 — Levantar el ambiente

```bash
docker compose up -d --build
```

La primera vez tarda 3–5 minutos (construye la imagen de Jupyter con todas las librerías).

### Paso 4 — Verificar

```bash
docker compose ps
```

Los tres servicios deben aparecer como `running` o `healthy`.

### Paso 5 — Acceder a las herramientas

- **Jupyter Lab:** http://localhost:8888/?token=`<JUPYTER_TOKEN>` (valor de tu `.env`)
- **Adminer:** http://localhost:8080
  - Sistema: `MySQL`
  - Servidor: `mysql` (¡no `localhost`!)
  - Usuario / contraseña / base: las de tu `.env`

### Paso 6 — Probar la conexión

Dentro de Jupyter, abre un notebook nuevo y ejecuta:

```python
from src.db import test_connection
test_connection()
```

Debe imprimir `Conexión OK`.

---

## 📂 Estructura del proyecto

```
construnorte-rotacion/
├── CLAUDE.md                       # Contexto para Claude Code
├── README.md                       # Este archivo
├── docker-compose.yml              # Orquestación Docker
├── .env.example                    # Plantilla de variables (sin secretos)
├── .gitignore
├── .claude/
│   └── skills/                     # Skills especializadas para Claude Code
│       ├── project-conventions/
│       ├── mysql-operations/
│       ├── etl-pipeline/
│       ├── feature-engineering/
│       ├── abc-xyz-classification/
│       ├── time-series-modeling/
│       ├── evaluation-metrics/
│       └── notebook-style/
├── docker/
│   └── jupyter/                    # Imagen custom de Jupyter
│       ├── Dockerfile
│       └── requirements.txt
├── db/
│   └── init/
│       └── 01_schema.sql           # Schema inicial autoejecutado
├── data/
│   ├── raw/                        # CSV original (gitignored)
│   └── processed/                  # Datasets intermedios (gitignored)
├── notebooks/                      # Notebooks numerados por CRISP-DM
├── src/                            # Código reutilizable
│   ├── db.py                       # Conexión a MySQL
│   ├── etl.py                      # Pipeline ETL
│   ├── features.py                 # Feature engineering
│   ├── abc_xyz.py                  # Clasificación ABC/XYZ
│   ├── models.py                   # Entrenamiento
│   └── evaluation.py               # Métricas
├── hop/                            # Flujos visuales de Apache Hop
├── reports/                        # Informe ejecutivo, figuras
├── dashboard/                      # Workbook de Tableau
└── docs/                           # Documentación del proyecto
```

---

## 📋 Flujo de trabajo (4 fases CRISP-DM)

| Fase | Notebooks | Resultado |
|---|---|---|
| **1. Comprensión** | `01_perfil_inicial`, `02_eda` | Diccionario de datos, hallazgos iniciales |
| **2. Preparación** | `03_preparacion`, `04_abc_xyz` | Tablas `ventas_semanales` y `clasificacion_abc_xyz` |
| **3. Modelado** | `05_baseline`, `06_lightgbm`, `07_xgboost`, `08_prophet` | Modelos entrenados y predicciones en `pronosticos` |
| **4. Evaluación** | `09_evaluacion_final` | Tabla `metricas_modelos`, dashboard en Tableau |

---

## 🔧 Comandos útiles

```bash
# Levantar todo
docker compose up -d

# Apagar (mantiene datos)
docker compose down

# Apagar y BORRAR la base (cuidado)
docker compose down -v

# Ver logs
docker compose logs -f mysql
docker compose logs -f jupyter

# Reconstruir Jupyter (tras cambiar requirements.txt)
docker compose build jupyter
docker compose up -d jupyter

# Entrar a MySQL por consola
docker exec -it construnorte_mysql mysql -u construnorte_user -p construnorte

# Entrar al contenedor de Jupyter
docker exec -it construnorte_jupyter bash

# Backup de la base
docker exec construnorte_mysql mysqldump -u root -p construnorte > backup.sql
```

---

## 🤖 Trabajar con Claude Code

Este proyecto está optimizado para colaborar con [Claude Code](https://docs.claude.com/en/docs/claude-code).

**Flujo recomendado:**

1. Abre Claude Code en la raíz del proyecto (lee `CLAUDE.md` automáticamente).
2. Para cada tarea nueva, indica: *"Lee primero la skill `<nombre>` antes de empezar."*
3. Las skills están en `.claude/skills/` con nombres descriptivos.

**Frase para iniciar sesiones:**
> *"Voy a trabajar en [TAREA]. Lee primero `CLAUDE.md` y la skill correspondiente, luego propón un plan en 5 pasos antes de escribir código."*

---

## 🔒 Privacidad y datos personales

El dataset contiene información protegida por la **Ley 1581 de 2012** de Colombia. Medidas:

- Columnas personales (`Cliente`, `Nombre Cliente`, `Cedula Vendedor`, etc.) **se eliminan en la primera fase del ETL**.
- El dataset modelable que se almacena en MySQL no contiene identificadores personales.
- Carta de autorización firmada por la organización beneficiaria (Anexo C del informe).
- El repositorio público **no contiene** el dataset original.

---

## 📅 Plazos

- **Inicio:** 1 de mayo de 2026
- **Entrega:** 28 de mayo de 2026
- **Duración:** 4 semanas

---

## 📄 Licencia

Proyecto académico. Datos de uso restringido. © 2026 — Unicomfacauca.
