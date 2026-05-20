# 09 — Diseño del Frontend

**Documento técnico para la implementación del frontend mini del proyecto ConstruNorte.**

**Audiencia:** Claude Code (debe usar el skill `frontend-design`).
**Versión:** 1.0 — mayo 2026.
**Autores:** Diego Andrés De Jesús Montenegro y Luis David Andrade Díaz.

---

## 1. Propósito

Construir una página web de **una sola pantalla** que consuma la API REST del proyecto y muestre los resultados de forma profesional durante la sustentación.

**Reemplaza:** Mostrar queries SQL en pantalla.
**Por:** Una interfaz visual que muestra las mismas consultas con buen diseño.

**No es objetivo:**
- No es un dashboard exhaustivo (eso lo hará Tableau).
- No es una SPA con routing complejo.
- No requiere autenticación.

---

## 2. Stack técnico (sin build tools)

| Componente | Tecnología | CDN |
|---|---|---|
| HTML | HTML5 semántico | - |
| CSS | **Tailwind CSS** | `https://cdn.tailwindcss.com` |
| Interactividad | **Alpine.js** | `https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js` |
| Gráficos | **Chart.js** | `https://cdn.jsdelivr.net/npm/chart.js` |
| Iconos | **Lucide Icons (web component)** | CDN |
| Fuente | **Inter** (Google Fonts) | - |

**Sin webpack, sin npm, sin build.** Todo desde CDN. El frontend es 3 archivos.

---

## 3. Identidad visual

### 3.1 Paleta de colores

Mantener consistencia con los notebooks (Tailwind classes):

| Uso | Color hex | Tailwind class |
|---|---|---|
| Primario (azul corporativo) | `#1F4E78` | `bg-[#1F4E78]` / `text-[#1F4E78]` |
| Acento naranja (baseline) | `#E67E22` | `bg-[#E67E22]` |
| Verde éxito | `#27AE60` | `bg-emerald-600` |
| Rojo alerta | `#C0392B` | `bg-red-600` |
| Morado LightGBM | `#9B59B6` | `bg-purple-500` |
| Verde-azul XGBoost | `#16A085` | `bg-teal-600` |
| Rosa Prophet | `#E91E63` | `bg-pink-500` |
| Fondo | `#0F172A` (slate-900) | `bg-slate-900` |
| Texto principal | `#F1F5F9` (slate-100) | `text-slate-100` |
| Texto secundario | `#94A3B8` (slate-400) | `text-slate-400` |
| Borde sutil | `#1E293B` (slate-800) | `border-slate-800` |

**Tema:** Dark mode (mejor para sustentaciones, ahorra batería del proyector).

### 3.2 Tipografía

- Familia: **Inter** (limpia, profesional).
- Tamaños:
  - Headings principales: `text-3xl font-bold`
  - Subheadings: `text-xl font-semibold`
  - Body: `text-base`
  - Captions: `text-sm text-slate-400`
- Números grandes (KPIs): `text-4xl font-bold tabular-nums`

### 3.3 Espaciado

- Padding base de secciones: `p-6`
- Gap entre cards: `gap-4` o `gap-6`
- Border radius: `rounded-xl` (12px) — moderno pero sobrio.

### 3.4 Estilo visual general

- **Cards** con `bg-slate-800/50 border border-slate-700 backdrop-blur` (efecto glassmorphism sutil).
- **Sombras** suaves: `shadow-lg shadow-black/20`.
- **Transiciones** en hover: `transition-all duration-200`.
- **Sin emojis** en la UI (mantener profesional).
- Iconos Lucide para identificar secciones.

⚠️ **EVITAR a toda costa:**
- Gradientes coloridos.
- Animaciones excesivas.
- Sombras pronunciadas.
- Bordes redondeados extremos (`rounded-full` en cards).
- Colores fluorescentes.

---

## 4. Estructura de la página

Página única con **navegación por tabs** (sin recargar):

```
┌─────────────────────────────────────────────────────────┐
│ HEADER                                                   │
│ ConstruNorte — Sistema de Pronóstico de Demanda          │
│ Proyecto Diplomado Unicomfacauca · 2026                  │
├─────────────────────────────────────────────────────────┤
│ TABS                                                     │
│ [Resumen] [Pronósticos] [Modelos] [Clasificación] [Alertas]
├─────────────────────────────────────────────────────────┤
│ CONTENT (cambia según tab activo)                        │
│                                                          │
│ ...                                                      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Sección 1 — Resumen (tab por defecto)

**Propósito:** Vista panorámica del estado del modelo y del negocio.

### Layout:

```
Row 1: 4 KPI cards (grid de 4 columnas en desktop, 2 en tablet, 1 en mobile)
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │ SKUs   │ │ Modelo │ │ MAE    │ │ Mejora │
  │ activos│ │ recom. │ │ test   │ │ vs base│
  │ 2,310  │ │LightGBM│ │ 6.77   │ │ 79.18% │
  └────────┘ └────────┘ └────────┘ └────────┘

Row 2: Gráfico de barras horizontal — Comparación 4 modelos
  ┌─────────────────────────────────────────────┐
  │ MAE en Test 2026 — Comparación de modelos    │
  │ Baseline   ████████████████████████  525.09  │
  │ Prophet    █████████████████████████ 711.78  │
  │ XGBoost    ███████        167.23              │
  │ LightGBM   ███           86.67    ⭐ Mejor    │
  └─────────────────────────────────────────────┘

Row 3: 2 cards lado a lado
  ┌────────────────────┐ ┌────────────────────┐
  │ Top 5 SKUs estrella│ │ Distribución ABC   │
  │ (lista)            │ │ (donut chart)      │
  └────────────────────┘ └────────────────────┘
```

### Datos consumidos:

- `GET /api/clasificacion/resumen` (KPIs y donut)
- `GET /api/metricas/comparacion?split=test_2026` (barras)

---

## 6. Sección 2 — Pronósticos

**Propósito:** Consultar predicciones del modelo recomendado.

### Layout:

```
Row 1: Selectores
  ┌─────────────────────────────────────────────┐
  │ Semana: [2026-01-05 ▼]  Centro: [Todos ▼]   │
  │ Top: [20 ▼]              [Buscar SKU: ___]  │
  └─────────────────────────────────────────────┘

Row 2: Tabla principal
  ┌─────────────────────────────────────────────┐
  │ Top SKUs pronosticados — semana 2026-01-05  │
  ├───┬────────┬──────────────┬────────┬────────┤
  │ # │ Código │ Producto     │ Centro │ Pronós │
  ├───┼────────┼──────────────┼────────┼────────┤
  │ 1 │ 000041 │ CEMENTO GRIS │ 001    │ 3,250  │
  │ 2 │ 000291 │ VARILLA 1/2  │ 001    │ 1,890  │
  │...│        │              │        │        │
  └─────────────────────────────────────────────┘
```

**Comportamiento:**
- Cambiar selectores re-consulta el endpoint.
- Click en una fila abre un panel lateral (drawer) con la gráfica del SKU.

### Gráfica al click de SKU:

```
┌────────────────────────────────────────────┐
│ SKU 000041 — CEMENTO GRIS *50 KL T1 ARGOS  │
│ Clase ABC: A  Segmento: AX                  │
│                                             │
│ [Gráfica de línea: real + LightGBM + base] │
│                                             │
│ [Cerrar]                                    │
└────────────────────────────────────────────┘
```

### Datos consumidos:

- `GET /api/pronosticos/top` (tabla principal).
- `GET /api/pronosticos/sku/{item}` (gráfica al click).

---

## 7. Sección 3 — Modelos

**Propósito:** Mostrar el análisis comparativo de los 4 modelos (la "carta de venta" del proyecto).

### Layout:

```
Row 1: Selectores
  ┌─────────────────────────────────────────────┐
  │ Split: [test_2026 ▼]  Segmento: [global ▼]  │
  └─────────────────────────────────────────────┘

Row 2: Tabla de métricas
  ┌─────────────────────────────────────────────────┐
  │ Comparación de modelos                           │
  ├──────────┬──────┬──────┬──────┬─────┬───────────┤
  │ Modelo   │ MAE  │ RMSE │ MAPE │SMAPE│ Mejora    │
  ├──────────┼──────┼──────┼──────┼─────┼───────────┤
  │ Baseline │ 32.5 │ 389  │ 170% │ 147%│ -         │
  │ LightGBM │ 6.77 │ 145  │ 28%  │ 142%│ +79% ⭐   │
  │ XGBoost  │ 13.2 │ 258  │ 56%  │ 147%│ +59%      │
  └─────────────────────────────────────────────────┘

Row 3: Gráfica radar comparando los 4 modelos en 4 métricas
```

### Datos consumidos:

- `GET /api/metricas/comparacion`.

---

## 8. Sección 4 — Clasificación

**Propósito:** Vista descriptiva del portafolio (Tema 1 del proyecto).

### Layout:

```
Row 1: KPIs (4 cards)
  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
  │ Total  │ │ Clase A│ │ % valor│ │ SKUs CZ│
  │ 2,310  │ │ 97     │ │ 79.3%  │ │ 1,745  │
  └────────┘ └────────┘ └────────┘ └────────┘

Row 2: Heatmap de la matriz ABC × XYZ
  ┌─────────────────────────────────────────────┐
  │     X     Y     Z                            │
  │ A   4    47    46                            │
  │ B   16  105   244                            │
  │ C   7   166  1745                            │
  └─────────────────────────────────────────────┘
  (Colores: verde claro → rojo intenso según conteo)

Row 3: Tabla de top SKUs estrella (AX, AY)
```

### Datos consumidos:

- `GET /api/clasificacion/resumen`.

---

## 9. Sección 5 — Insights y Alertas

**Propósito:** Información accionable para el negocio.

### Layout:

```
Row 1: Tabs internas
  [Crecimiento proyectado] [Alertas de cambio drástico]

Row 2 (si tab Crecimiento):
  Tabla con top 15 SKUs con mayor crecimiento %.
  Indicadores visuales: ⬆ verde para crecimiento, ⬇ rojo decrecimiento.

Row 2 (si tab Alertas):
  Cards de alertas, ordenadas por severidad.
  ┌──────────────────────────────────────────┐
  │ 🔴 ALTA  SKU 000XXX                       │
  │ Pico proyectado: 250% sobre histórico     │
  │ Acción: Revisar disponibilidad de stock   │
  └──────────────────────────────────────────┘
```

### Datos consumidos:

- `GET /api/insights/crecimiento`.
- `GET /api/insights/alertas`.

---

## 10. Comportamiento general

### 10.1 Estado global con Alpine.js

```html
<div x-data="{
  activeTab: 'resumen',
  loading: false,
  // ... más estado
}">
```

### 10.2 Loading states

Mientras se carga un endpoint, mostrar un skeleton loader (no un spinner genérico):

```html
<div class="animate-pulse bg-slate-700 h-12 rounded"></div>
```

### 10.3 Error handling

Si un fetch falla, mostrar un mensaje sobrio:

```html
<div class="bg-red-900/30 border border-red-700 rounded-lg p-4">
  <p class="text-red-300">No se pudieron cargar los datos. Verifica que el API esté corriendo.</p>
</div>
```

### 10.4 Responsive

- **Desktop (>1024px):** Layouts completos como se describen.
- **Tablet (640-1024px):** Grids de 4 → 2 columnas.
- **Mobile (<640px):** 1 columna, tabs scrolleables horizontalmente.

---

## 11. Detalles importantes para Claude Code

### 11.1 Activar el skill `frontend-design`

El frontend debe construirse con principios de diseño profesional. **NO usar templates genéricos de Bootstrap o Material UI defaults.** Cada elemento debe sentirse intencional.

### 11.2 No usar Vue, React, Svelte ni similares

Alpine.js es suficiente. Si el código requiere algo más complejo, primero **simplificar el diseño**, no agregar herramientas.

### 11.3 Iconos

Usar **Lucide Icons** vía web component:

```html
<script src="https://unpkg.com/lucide@latest"></script>
<i data-lucide="trending-up"></i>
<script>lucide.createIcons();</script>
```

Iconos a usar:
- `bar-chart-3` para Resumen
- `trending-up` para Pronósticos
- `git-compare` para Modelos
- `layers` para Clasificación
- `alert-triangle` para Alertas

### 11.4 Animaciones sobrias

Solo `transition-colors`, `transition-transform` cuando aporten valor. **NO** animaciones de entrada/salida exageradas.

### 11.5 Accesibilidad mínima

- Contraste de texto sobre fondo: cumplir AA WCAG.
- `aria-label` en botones de icono.
- `<label>` para todos los inputs.

---

## 12. Estructura de archivos del frontend

```
api/static/
├── index.html           # ~250 líneas, una sola página
├── app.js               # ~300 líneas, lógica Alpine + fetch
└── styles.css           # ~30 líneas, sólo overrides necesarios
```

**Es deliberadamente pequeño.** Si crece más, simplificar.

---

## 13. Criterios de aceptación visuales

El frontend se considera completo cuando:

- [ ] Las 5 secciones funcionan y consumen sus endpoints.
- [ ] Tema oscuro consistente con la paleta definida.
- [ ] Responsive en desktop y tablet (mobile opcional).
- [ ] Sin emojis en la UI (excepto en mensajes de alerta tipo `🔴 ALTA`).
- [ ] Loading states con skeletons (no spinners).
- [ ] Tipografía Inter cargada correctamente.
- [ ] Iconos Lucide visibles donde corresponde.
- [ ] **NO se ve como template gratis ni como Bootstrap default.**
