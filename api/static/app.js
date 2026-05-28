'use strict';

// ── Constantes ────────────────────────────────────────────────────────────────

const COLORES = {
  primario:   '#1F4E78',
  baseline:   '#E67E22',
  lightgbm:   '#9B59B6',
  xgboost:    '#16A085',
  prophet:    '#E91E63',
  verde:      '#27AE60',
  rojo:       '#C0392B',
  slate400:   '#94A3B8',
  slate700:   '#334155',
  slate800:   '#1E293B',
};

const NOMBRES_MODELO = {
  baseline_ma4: 'Baseline (MA-4)',
  lightgbm:     'LightGBM',
  xgboost:      'XGBoost',
  prophet:      'Prophet',
};

const COLOR_MODELO = {
  baseline_ma4: COLORES.baseline,
  lightgbm:     COLORES.lightgbm,
  xgboost:      COLORES.xgboost,
  prophet:      COLORES.prophet,
};

const NOMBRES_CENTRO = {
  '001': 'Ciudad Jardín',
  '002': 'Bello Horizonte Ppal',
  '003': 'Bello Horizonte Cerámicas',
};

const NOMBRES_CENTRO_CORTO = {
  '001': 'Ciudad Jardín',
  '002': 'B.H. Principal',
  '003': 'B.H. Cerámicas',
};

/** Devuelve el nombre legible de un centro, con fallback al código. */
function nombreCentro(codigo, corto = false) {
  if (!codigo) return '—';
  const mapa = corto ? NOMBRES_CENTRO_CORTO : NOMBRES_CENTRO;
  return mapa[codigo] || codigo;
}

const SEMANAS = [
  '2025-10-06','2025-10-13','2025-10-20','2025-10-27',
  '2025-11-03','2025-11-10','2025-11-17','2025-11-24',
  '2025-12-01','2025-12-08','2025-12-15','2025-12-22','2025-12-29',
  '2026-01-05','2026-01-12','2026-01-19','2026-01-26',
  '2026-02-02','2026-02-09','2026-02-16','2026-02-23',
  '2026-03-02','2026-03-09','2026-03-16','2026-03-23','2026-03-30',
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function configChart() {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = COLORES.slate400;
  Chart.defaults.borderColor = COLORES.slate800;
}

async function apiFetch(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

function fmt(n, decimals = 0) {
  if (n == null) return '—';
  return Number(n).toLocaleString('es-CO', { maximumFractionDigits: decimals });
}

function fmtPct(n) {
  if (n == null) return '—';
  return `${n > 0 ? '+' : ''}${Number(n).toFixed(1)}%`;
}

function fmtCOP(v) {
  if (v == null) return '—';
  if (v >= 1_000_000_000)
    return '$' + (v / 1_000_000).toLocaleString('es-CO', { maximumFractionDigits: 0 }) + 'M';
  if (v >= 1_000_000)
    return '$' + (v / 1_000_000).toLocaleString('es-CO', { maximumFractionDigits: 1 }) + 'M';
  if (v >= 1_000)
    return '$' + (v / 1_000).toLocaleString('es-CO', { maximumFractionDigits: 0 }) + 'K';
  return '$' + Number(v).toFixed(0);
}

function destroyChart(ref) {
  if (ref && typeof ref.destroy === 'function') ref.destroy();
}

// ── Componente Alpine ─────────────────────────────────────────────────────────

function app() {
  return {
    // ── navegación ──
    tab: 'resumen',
    loaded: {},
    tabs: [
      { id: 'resumen',       label: 'Resumen',        icon: 'bar-chart-3'    },
      { id: 'pronosticos',   label: 'Pronósticos',    icon: 'trending-up'    },
      { id: 'modelos',       label: 'Modelos',        icon: 'git-compare'    },
      { id: 'clasificacion', label: 'Clasificación',  icon: 'layers'         },
      { id: 'insights',      label: 'Insights',       icon: 'alert-triangle' },
    ],

    // ── resumen ──
    resumen:        null,             // /api/clasificacion/resumen (KPIs, ABC, etc.)
    metricasGlobal: null,             // /api/metricas/comparacion (MAE modelos)
    loadingRes:     false,
    errorRes:       null,

    // Filtros interactivos del Resumen
    resCentro:      '',               // '' = todos los centros
    resLinea:       '',               // '' = todas las líneas
    resTopN:        10,               // 5, 10, 20

    // Datos filtrables
    estacData:        null,           // /api/descriptivo/estacionalidad (filtrable centro)
    lineasPorCentro:  null,           // /api/descriptivo/lineas-por-centro (filtrable centro)
    topSkusCentro:    null,           // /api/descriptivo/top-skus-por-centro (centro+linea+limit)
    centrosCompara:   null,           // /api/descriptivo/ventas-por-centro (comparativa global)

    // Estado de recarga (para animaciones fade)
    reloadingFiltros: false,

    // Listado de líneas únicas para el selector
    lineasDisponibles: [],

    // ── pronósticos/top ──
    topData:        null,
    loadingTop:     false,
    errorTop:       null,
    topFecha:       '2026-01-05',
    topCentro:      '',
    topLimit:       20,
    semanas:        SEMANAS,

    // ── drawer sku ──
    drawerOpen:     false,
    skuData:        null,
    skuLoading:     false,
    skuError:       null,

    // ── modelos ──
    metricasData:   null,
    loadingMet:     false,
    errorMet:       null,
    metSplit:       'test_2026',
    metSegmento:    'global',

    // ── insights ──
    insightsTab:    'crecimiento',
    crecData:       null,
    loadingCrec:    false,
    errorCrec:      null,
    crecFecha:      '2026-01-05',
    crecSoloAB:     false,
    alertasData:    null,
    loadingAlertas: false,
    errorAlertas:   null,
    alertasFecha:   '2026-01-05',
    alertasUmbral:  100,
    alertasSoloAB:  true,

    // ── descriptivo ──
    centrosData:      null,           // volumen por centro para tab Pronósticos
    loadingCentros:   false,
    errorCentros:     null,
    paretoData:       null,
    loadingPareto:    false,
    errorPareto:      null,
    diamantesData:    null,
    loadingDiamantes: false,
    errorDiamantes:   null,

    // ── instancias de chart ──
    _skuChart:      null,
    _paretoChart:   null,

    // ─────────────────────────────────────────────────────────────────────────

    async init() {
      configChart();
      await this.loadResumen();
      this.$nextTick(() => {
        if (window.lucide) lucide.createIcons();
      });
    },

    async switchTab(t) {
      this.tab = t;
      this.$nextTick(() => { if (window.lucide) lucide.createIcons(); });
      if (this.loaded[t]) return;
      this.loaded[t] = true;
      switch (t) {
        case 'pronosticos':   await Promise.all([this.loadTop(), this.loadCentros()]); break;
        case 'modelos':       await this.loadMetricas(); break;
        case 'clasificacion': await this.loadPareto(); break;
        case 'insights':      await Promise.all([this.loadCrecimiento(), this.loadDiamantes()]); break;
      }
    },

    // ── Resumen ───────────────────────────────────────────────────────────────

    /** Carga inicial completa del Resumen. */
    async loadResumen() {
      this.loadingRes = true; this.errorRes = null;
      try {
        const [resumen, metricasGlobal, estacData, lineasPorCentro, topSkusCentro, centrosCompara] = await Promise.all([
          apiFetch('/api/clasificacion/resumen'),
          apiFetch('/api/metricas/comparacion?split=test_2026&segmento=global'),
          apiFetch(this._urlEstacionalidad()),
          apiFetch(this._urlLineasPorCentro()),
          apiFetch(this._urlTopSkusCentro()),
          apiFetch('/api/descriptivo/ventas-por-centro'),
        ]);
        this.resumen          = resumen;
        this.metricasGlobal   = metricasGlobal;
        this.estacData        = estacData;
        this.lineasPorCentro  = lineasPorCentro;
        this.topSkusCentro    = topSkusCentro;
        this.centrosCompara   = centrosCompara;

        // Extrae las líneas disponibles del primer load (vista global)
        if (lineasPorCentro?.items) {
          this.lineasDisponibles = lineasPorCentro.items.map(l => l.linea);
        }
      } catch (e) {
        this.errorRes = e.message;
      } finally {
        this.loadingRes = false;
      }
    },

    /** Construye URLs de los endpoints filtrables con el estado actual. */
    _urlEstacionalidad() {
      return this.resCentro
        ? `/api/descriptivo/estacionalidad?centro=${this.resCentro}`
        : '/api/descriptivo/estacionalidad';
    },
    _urlLineasPorCentro() {
      return this.resCentro
        ? `/api/descriptivo/lineas-por-centro?centro=${this.resCentro}`
        : '/api/descriptivo/lineas-por-centro';
    },
    _urlTopSkusCentro() {
      const params = new URLSearchParams({ limit: this.resTopN });
      if (this.resCentro) params.set('centro', this.resCentro);
      if (this.resLinea)  params.set('linea',  this.resLinea);
      return `/api/descriptivo/top-skus-por-centro?${params}`;
    },

    /** Recarga selectiva al cambiar el filtro de CENTRO.
     *  Afecta: estacionalidad, líneas por centro, top SKUs por centro. */
    async onCentroChange() {
      this.reloadingFiltros = true;
      this.errorRes = null;
      try {
        const [estac, lineas, topSkus] = await Promise.all([
          apiFetch(this._urlEstacionalidad()),
          apiFetch(this._urlLineasPorCentro()),
          apiFetch(this._urlTopSkusCentro()),
        ]);
        this.estacData       = estac;
        this.lineasPorCentro = lineas;
        this.topSkusCentro   = topSkus;
      } catch (e) {
        this.errorRes = e.message;
      } finally {
        setTimeout(() => { this.reloadingFiltros = false; }, 250);
      }
    },

    /** Recarga selectiva al cambiar el filtro de LÍNEA o de TOP N.
     *  Afecta solo: top SKUs por centro. */
    async onLineaOTopChange() {
      this.reloadingFiltros = true;
      this.errorRes = null;
      try {
        this.topSkusCentro = await apiFetch(this._urlTopSkusCentro());
      } catch (e) {
        this.errorRes = e.message;
      } finally {
        setTimeout(() => { this.reloadingFiltros = false; }, 200);
      }
    },

    /** Resetea todos los filtros del Resumen a sus valores por defecto. */
    async resetFiltros() {
      this.resCentro = '';
      this.resLinea  = '';
      this.resTopN   = 10;
      await this.onCentroChange();
    },

    get kpiMaeLightgbm() {
      if (!this.metricasGlobal) return null;
      return this.metricasGlobal.modelos.find(m => m.modelo === 'lightgbm')?.mae;
    },
    get kpiMejora() {
      if (!this.metricasGlobal) return null;
      return this.metricasGlobal.modelos.find(m => m.modelo === 'lightgbm')?.mejora_vs_baseline_pct;
    },

    barModelos() {
      if (!this.metricasGlobal) return [];
      const modelos = this.metricasGlobal.modelos
        .filter(m => m.modelo !== 'prophet')
        .sort((a, b) => b.mae - a.mae);
      const maxMae = Math.max(...modelos.map(m => m.mae));
      return modelos.map(m => ({
        modeloKey: m.modelo,
        nombre: NOMBRES_MODELO[m.modelo] || m.nombre_amigable,
        mae:    m.mae,
        pct:    Math.round((m.mae / maxMae) * 100),
        color:  COLOR_MODELO[m.modelo] || COLORES.slate700,
      }));
    },

    get barrasABC() {
      if (!this.resumen?.distribucion_abc) return [];
      const dist = this.resumen.distribucion_abc;
      return ['A', 'B', 'C'].map(clase => ({
        clase,
        color:      COLORS_ABC[clase],
        num_skus:   (dist[clase]?.num_skus || 0).toLocaleString('es-CO'),
        porcentaje: (dist[clase]?.porcentaje_skus || 0).toFixed(1),
      }));
    },

    // ── Pronósticos ───────────────────────────────────────────────────────────

    async loadTop() {
      this.loadingTop = true; this.errorTop = null;
      try {
        const params = new URLSearchParams({
          fecha: this.topFecha,
          limit: this.topLimit,
          modelo: 'lightgbm',
        });
        if (this.topCentro) params.set('centro', this.topCentro);
        this.topData = await apiFetch(`/api/pronosticos/top?${params}`);
      } catch (e) {
        this.errorTop = e.message;
      } finally {
        this.loadingTop = false;
      }
    },

    async openSKU(item) {
      this.drawerOpen = true;
      this.skuLoading = true;
      this.skuData = null;
      this.skuError = null;
      destroyChart(this._skuChart);
      try {
        this.skuData = await apiFetch(`/api/pronosticos/sku/${item}`);
        this.$nextTick(() => this.initSkuChart());
      } catch (e) {
        this.skuError = e.message;
      } finally {
        this.skuLoading = false;
      }
    },

    closeSKU() {
      this.drawerOpen = false;
      destroyChart(this._skuChart);
      this._skuChart = null;
    },

    initSkuChart() {
      const canvas = document.getElementById('skuChart');
      if (!canvas || !this.skuData) return;
      destroyChart(this._skuChart);
      const serie = this.skuData.serie;
      const labels = serie.map(p => p.fecha.slice(5));  // MM-DD
      const real   = serie.map(p => p.cantidad_real);
      const pred   = serie.map(p => p.cantidad_predicha_principal);
      const base   = serie.map(p => p.cantidad_predicha_baseline);

      this._skuChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Real',
              data: real,
              borderColor: '#60a5fa',
              backgroundColor: 'rgba(96,165,250,0.08)',
              borderWidth: 1.8,
              pointRadius: 0,
              tension: 0.3,
              fill: true,
              spanGaps: false,
            },
            {
              label: 'LightGBM',
              data: pred,
              borderColor: COLORES.lightgbm,
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.3,
              spanGaps: false,
            },
            {
              label: 'Baseline',
              data: base,
              borderColor: COLORES.baseline,
              borderWidth: 1.5,
              borderDash: [4, 3],
              pointRadius: 0,
              tension: 0.3,
              spanGaps: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { labels: { color: COLORES.slate400, boxWidth: 18, font: { size: 11 } } },
          },
          scales: {
            x: { grid: { color: COLORES.slate800 }, ticks: { color: COLORES.slate400, maxTicksLimit: 12, maxRotation: 45 } },
            y: { grid: { color: COLORES.slate800 }, ticks: { color: COLORES.slate400 } },
          },
        },
      });
    },

    // ── Modelos ───────────────────────────────────────────────────────────────

    async loadMetricas() {
      this.loadingMet = true; this.errorMet = null;
      try {
        const params = new URLSearchParams({ split: this.metSplit, segmento: this.metSegmento });
        this.metricasData = await apiFetch(`/api/metricas/comparacion?${params}`);
      } catch (e) {
        this.errorMet = e.message;
        this.metricasData = null;
      } finally {
        this.loadingMet = false;
      }
    },

    bestMae() {
      if (!this.metricasData) return Infinity;
      return Math.min(...this.metricasData.modelos.map(m => m.mae));
    },

    // ── Clasificación ─────────────────────────────────────────────────────────

    heatCell(abc, xyz) {
      if (!this.resumen) return { num_skus: 0, valor_total: 0 };
      return this.resumen.matriz_segmentos.find(s => s.clase_abc === abc && s.clase_xyz === xyz)
        || { num_skus: 0, valor_total: 0 };
    },

    heatStyle(abc, xyz) {
      const hex = COLORS_SEGMENTO[abc + xyz] || '#334155';
      if (!this.resumen) return `background-color: ${hex}1a`;
      const maxSkus = Math.max(...this.resumen.matriz_segmentos.map(s => s.num_skus));
      const cell    = this.heatCell(abc, xyz);
      const ratio   = maxSkus > 0 ? cell.num_skus / maxSkus : 0;
      const alpha   = (0.30 + ratio * 0.65).toFixed(2);
      const r = parseInt(hex.slice(1, 3), 16);
      const g = parseInt(hex.slice(3, 5), 16);
      const b = parseInt(hex.slice(5, 7), 16);
      return `background-color: rgba(${r}, ${g}, ${b}, ${alpha})`;
    },

    // ── Insights ──────────────────────────────────────────────────────────────

    async loadCrecimiento() {
      this.loadingCrec = true; this.errorCrec = null;
      try {
        const params = new URLSearchParams({
          fecha_objetivo: this.crecFecha,
          limit: 15,
          solo_clase_ab: this.crecSoloAB,
        });
        this.crecData = await apiFetch(`/api/insights/crecimiento?${params}`);
      } catch (e) {
        this.errorCrec = e.message;
      } finally {
        this.loadingCrec = false;
      }
    },

    async loadAlertas() {
      this.loadingAlertas = true; this.errorAlertas = null;
      try {
        const params = new URLSearchParams({
          fecha_objetivo: this.alertasFecha,
          umbral_cambio_pct: this.alertasUmbral,
          solo_clase_ab: this.alertasSoloAB,
        });
        this.alertasData = await apiFetch(`/api/insights/alertas?${params}`);
      } catch (e) {
        this.errorAlertas = e.message;
      } finally {
        this.loadingAlertas = false;
      }
    },

    // ── Descriptivo ───────────────────────────────────────────────────────────

    async loadCentros() {
      this.loadingCentros = true; this.errorCentros = null;
      try {
        this.centrosData = await apiFetch('/api/descriptivo/ventas-por-centro');
      } catch (e) {
        this.errorCentros = e.message;
      } finally {
        this.loadingCentros = false;
      }
    },

    async loadPareto() {
      this.loadingPareto = true; this.errorPareto = null;
      try {
        this.paretoData = await apiFetch('/api/descriptivo/pareto');
        this.$nextTick(() => this.initParetoChart());
      } catch (e) {
        this.errorPareto = e.message;
      } finally {
        this.loadingPareto = false;
      }
    },

    async loadDiamantes() {
      this.loadingDiamantes = true; this.errorDiamantes = null;
      try {
        this.diamantesData = await apiFetch('/api/descriptivo/diamantes');
      } catch (e) {
        this.errorDiamantes = e.message;
      } finally {
        this.loadingDiamantes = false;
      }
    },

    initParetoChart() {
      const canvas = document.getElementById('paretoChart');
      if (!canvas || !this.paretoData) return;
      destroyChart(this._paretoChart);
      const puntos = this.paretoData.puntos;
      this._paretoChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: puntos.map(p => p.pct_skus.toFixed(0) + '%'),
          datasets: [
            {
              label: 'Valor acumulado',
              data: puntos.map(p => p.pct_valor_acum),
              borderColor: COLORES.primario,
              backgroundColor: 'rgba(31,78,120,0.15)',
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.35,
              fill: true,
            },
            {
              label: 'Referencia 80%',
              data: puntos.map(() => 80),
              borderColor: COLORES.baseline,
              borderWidth: 1.5,
              borderDash: [5, 4],
              pointRadius: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { labels: { color: COLORES.slate400, boxWidth: 14, font: { size: 11 } } },
            tooltip: {
              callbacks: {
                title: items => items[0].label + ' de SKUs',
                label: item => item.dataset.label + ': ' + item.parsed.y.toFixed(1) + '%',
              },
            },
          },
          scales: {
            x: {
              grid: { color: COLORES.slate800 },
              ticks: { color: COLORES.slate400, maxTicksLimit: 10 },
              title: { display: true, text: '% SKUs (mayor → menor valor)', color: COLORES.slate400, font: { size: 10 } },
            },
            y: {
              min: 0, max: 100,
              grid: { color: COLORES.slate800 },
              ticks: { color: COLORES.slate400, callback: v => v + '%' },
              title: { display: true, text: '% valor acumulado', color: COLORES.slate400, font: { size: 10 } },
            },
          },
        },
      });
    },

    // ── Transformadores para gráficas dinámicas del Resumen ─────────────────

    /** Barras de Top líneas por centro (ya filtradas en el backend). */
    barrasLineasPorCentro() {
      const data = this.lineasPorCentro?.items;
      if (!data?.length) return [];
      const maxVal = Math.max(...data.map(l => l.valor_total));
      return data.map((l, idx) => ({
        linea:        l.linea.length > 28 ? l.linea.slice(0, 28) + '…' : l.linea,
        lineaFull:    l.linea,
        valor_total:  l.valor_total,
        cantidad:     l.cantidad_total,
        num_skus:     l.num_skus_activos,
        pct_valor:    l.pct_valor,
        pct:          maxVal > 0 ? Math.round((l.valor_total / maxVal) * 100) : 0,
        opacity:      (1 - (idx / data.length) * 0.5).toFixed(2),
      }));
    },

    /** Filas de Top SKUs por centro. */
    filasTopSkusCentro() {
      const data = this.topSkusCentro?.items;
      if (!data?.length) return [];
      const maxVal = Math.max(...data.map(s => s.valor_total));
      return data.map(s => ({
        ...s,
        pct: maxVal > 0 ? Math.round((s.valor_total / maxVal) * 100) : 0,
      }));
    },

    /** Barras de comparativa entre centros (solo cuando filtro = "todos"). */
    barrasComparaCentros() {
      const data = this.centrosCompara?.items;
      if (!data?.length) return [];
      const maxVal = Math.max(...data.map(c => c.cantidad_total));
      return data.map(c => ({
        codigo:        c.centro_operacion,
        nombre:        this.nombreCentro(c.centro_operacion),
        cantidad:      c.cantidad_total,
        valor_total:   c.valor_total,
        pct_cantidad:  c.pct_cantidad,
        pct:           maxVal > 0 ? Math.round((c.cantidad_total / maxVal) * 100) : 0,
      }));
    },

    tooltipLineaCentro(item) {
      return [
        `Línea: ${item.lineaFull}`,
        `Valor total: ${fmtCOP(item.valor_total)}`,
        `Cantidad: ${fmt(item.cantidad)} uds`,
        `Participación: ${item.pct_valor.toFixed(1)}%`,
        `SKUs activos: ${fmt(item.num_skus)}`,
      ].join('\n');
    },

    tooltipSKUCentro(sku) {
      const lines = [
        `Código: ${sku.item}`,
        `Producto: ${sku.nombre}`,
      ];
      if (sku.linea)            lines.push(`Línea: ${sku.linea}`);
      if (sku.clase_abc)        lines.push(`Clase ABC: ${sku.clase_abc}`);
      if (sku.segmento_abc_xyz) lines.push(`Segmento: ${sku.segmento_abc_xyz}`);
      lines.push(`Cantidad: ${fmt(sku.cantidad_total)} uds`);
      lines.push(`Valor: ${fmtCOP(sku.valor_total)}`);
      return lines.join('\n');
    },

    tooltipCentroCompara(c) {
      return [
        `Centro: ${c.nombre}`,
        `Cantidad total: ${fmt(c.cantidad)} uds`,
        `Valor total: ${fmtCOP(c.valor_total)}`,
        `Participación: ${c.pct_cantidad.toFixed(1)}%`,
      ].join('\n');
    },

    estacBars() {
      if (!this.estacData?.items?.length) return [];
      const vals = this.estacData.items.map(p => p.cantidad_total_mes);
      const maxVal = Math.max(...vals);
      const minVal = Math.min(...vals);
      return this.estacData.items.map(p => ({
        ...p,
        pct: maxVal > 0 ? Math.round((p.cantidad_total_mes / maxVal) * 100) : 0,
        isPico: p.cantidad_total_mes === maxVal,
        isBajo: p.cantidad_total_mes === minVal,
      }));
    },

    centrosBars() {
      if (!this.centrosData?.items?.length) return [];
      const maxVal = Math.max(...this.centrosData.items.map(c => c.cantidad_total));
      const colors = ['#1F4E78', '#16A085', '#6366F1'];
      return this.centrosData.items.map((c, idx) => ({
        ...c,
        pct: maxVal > 0 ? Math.round((c.cantidad_total / maxVal) * 100) : 0,
        color: colors[idx % colors.length],
      }));
    },

    diamantesBars() {
      if (!this.diamantesData?.items?.length) return [];
      const maxVal = Math.max(...this.diamantesData.items.map(d => d.valor_total));
      return this.diamantesData.items.map(d => ({
        ...d,
        pct: maxVal > 0 ? Math.round((d.valor_total / maxVal) * 100) : 0,
        color: (typeof COLORS_SEGMENTO !== 'undefined' && COLORS_SEGMENTO[d.segmento]) || '#64748B',
      }));
    },

    switchInsightsTab(t) {
      this.insightsTab = t;
      if (t === 'crecimiento' && !this.crecData) this.loadCrecimiento();
      if (t === 'alertas'     && !this.alertasData) this.loadAlertas();
    },

    // ── Helpers UI ────────────────────────────────────────────────────────────
    fmt,
    fmtPct,
    fmtCOP,

    badgeABC(clase) {
      return clase === 'A' ? 'badge-a' : clase === 'B' ? 'badge-b' : 'badge-c';
    },
    badgeSeveridad(sev) {
      return sev === 'alta' ? 'badge-alta' : sev === 'media' ? 'badge-media' : 'badge-baja';
    },
    flechaCambio(pct) {
      return pct > 10 ? '▲' : pct < -10 ? '▼' : '─';
    },
    colorCambio(pct) {
      return pct > 10 ? 'text-emerald-400' : pct < -10 ? 'text-red-400' : 'text-slate-400';
    },

    // ── Tooltips enriquecidos para barras CSS del Resumen ────────────────────

    tooltipLinea(item) {
      return [
        `Línea: ${item.linea}`,
        `Valor total: ${fmtCOP(item.valor_total)}`,
        `Participación: ${item.pct_valor.toFixed(1)}%`,
        `SKUs en la línea: ${fmt(item.num_skus)}`,
      ].join('\n');
    },

    tooltipModelo(modeloKey) {
      if (!this.metricasGlobal) return '';
      const m = this.metricasGlobal.modelos.find(x => x.modelo === modeloKey);
      if (!m) return '';
      const lines = [
        `Modelo: ${NOMBRES_MODELO[m.modelo] || m.nombre_amigable}`,
        `MAE: ${m.mae.toFixed(2)} uds`,
        `RMSE: ${m.rmse.toFixed(2)}`,
        `MAPE: ${m.mape.toFixed(1)}%`,
      ];
      if (m.mejora_vs_baseline_pct != null) {
        lines.push(`Mejora vs Baseline: +${m.mejora_vs_baseline_pct.toFixed(2)}%`);
      }
      lines.push(`Predicciones evaluadas: ${fmt(m.n_obs)}`);
      return lines.join('\n');
    },

    tooltipABC(clase) {
      if (!this.resumen?.distribucion_abc) return '';
      const d = this.resumen.distribucion_abc[clase];
      if (!d) return '';
      return [
        `Clase ${clase}`,
        `SKUs: ${fmt(d.num_skus)} (${d.porcentaje_skus.toFixed(1)}%)`,
        `Valor total: ${fmtCOP(d.valor_total)}`,
        `Participación del valor: ${d.porcentaje_valor.toFixed(1)}%`,
      ].join('\n');
    },

    tooltipSKU(sku) {
      return [
        `Código: ${sku.item}`,
        `Producto: ${sku.nombre}`,
        `Valor histórico: ${fmtCOP(sku.valor_total)}`,
        `Clase: A · Segmento estrella (AX/AY)`,
      ].join('\n');
    },

    // ── Helpers de presentación de centros ──────────────────────────────────

    /** Nombre legible de un centro (e.g. '002' → 'Bello Horizonte Ppal'). */
    nombreCentro(codigo) {
      return nombreCentro(codigo, false);
    },

    /** Nombre corto de un centro (para espacios reducidos). */
    nombreCentroCorto(codigo) {
      return nombreCentro(codigo, true);
    },
  };
}
