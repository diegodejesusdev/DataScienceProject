-- ============================================================
-- Esquema inicial — Proyecto ConstruNorte
-- Se ejecuta automáticamente al primer arranque de MySQL en Docker
-- ============================================================

USE construnorte;

-- ============================================================
-- 1. ventas_crudas — datos transaccionales sin agregar
-- Granularidad: 1 fila = 1 línea de remisión/venta
-- ============================================================
CREATE TABLE IF NOT EXISTS ventas_crudas (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    fecha DATE NOT NULL,
    item VARCHAR(50) NOT NULL,
    nombre_item VARCHAR(255),
    referencia_item VARCHAR(100),
    codigo_barra VARCHAR(50),
    unidad_inventario VARCHAR(20),
    proveedor_codigo VARCHAR(50),
    proveedor_nombre VARCHAR(255),
    nombre_linea_n1 VARCHAR(100),
    nombre_linea_n2 VARCHAR(100),
    centro_operacion VARCHAR(20),
    tipo_documento VARCHAR(20),
    cantidad DECIMAL(18,4),
    precio_unitario DECIMAL(18,4),
    valor_bruto DECIMAL(18,4),
    valor_costo DECIMAL(18,4),
    peso DECIMAL(18,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fecha (fecha),
    INDEX idx_item (item),
    INDEX idx_fecha_item (fecha, item),
    INDEX idx_centro (centro_operacion),
    INDEX idx_tipo_doc (tipo_documento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. dim_producto — dimensión de productos (un SKU por fila)
-- ============================================================
CREATE TABLE IF NOT EXISTS dim_producto (
    item VARCHAR(50) PRIMARY KEY,
    nombre_item VARCHAR(255),
    referencia_item VARCHAR(100),
    unidad_inventario VARCHAR(20),
    proveedor_codigo VARCHAR(50),
    proveedor_nombre VARCHAR(255),
    nombre_linea_n1 VARCHAR(100),
    nombre_linea_n2 VARCHAR(100),
    fecha_primera_venta DATE,
    fecha_ultima_venta DATE,
    activo TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_linea_n1 (nombre_linea_n1),
    INDEX idx_proveedor (proveedor_codigo),
    INDEX idx_activo (activo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. ventas_semanales — tabla de hechos agregada (modelable)
-- Granularidad: SKU x Centro x Año x Semana
-- ============================================================
CREATE TABLE IF NOT EXISTS ventas_semanales (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    item VARCHAR(50) NOT NULL,
    centro_operacion VARCHAR(20),
    anio SMALLINT NOT NULL,
    semana TINYINT NOT NULL,
    fecha_inicio_semana DATE NOT NULL,
    cantidad_total DECIMAL(18,4),
    valor_bruto_total DECIMAL(18,4),
    num_transacciones INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_item_centro_semana (item, centro_operacion, anio, semana),
    INDEX idx_fecha_inicio (fecha_inicio_semana),
    INDEX idx_item (item),
    INDEX idx_item_fecha (item, fecha_inicio_semana)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. clasificacion_abc_xyz — clasificación de SKUs
-- ============================================================
CREATE TABLE IF NOT EXISTS clasificacion_abc_xyz (
    item VARCHAR(50) PRIMARY KEY,
    valor_total_periodo DECIMAL(18,4),
    porcentaje_acumulado DECIMAL(5,2),
    clase_abc CHAR(1),
    coef_variacion DECIMAL(10,4),
    clase_xyz CHAR(1),
    segmento_abc_xyz VARCHAR(2),
    fecha_calculo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_clase_abc (clase_abc),
    INDEX idx_clase_xyz (clase_xyz),
    INDEX idx_segmento (segmento_abc_xyz)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. pronosticos — predicciones generadas por los modelos
-- ============================================================
CREATE TABLE IF NOT EXISTS pronosticos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    item VARCHAR(50) NOT NULL,
    centro_operacion VARCHAR(20),
    fecha_inicio_semana DATE NOT NULL,
    modelo VARCHAR(50) NOT NULL,
    prediccion DECIMAL(18,4),
    limite_inferior DECIMAL(18,4),
    limite_superior DECIMAL(18,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_item_modelo (item, modelo),
    INDEX idx_fecha (fecha_inicio_semana),
    INDEX idx_modelo (modelo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. metricas_modelos — evaluación de los modelos
-- ============================================================
CREATE TABLE IF NOT EXISTS metricas_modelos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    modelo VARCHAR(50) NOT NULL,
    segmento_abc_xyz VARCHAR(10),
    mae DECIMAL(12,4),
    rmse DECIMAL(12,4),
    mape DECIMAL(12,4),
    smape DECIMAL(12,4),
    num_skus INT,
    num_observaciones INT,
    horizonte_semanas TINYINT,
    fecha_evaluacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_modelo (modelo),
    INDEX idx_segmento (segmento_abc_xyz)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Vista útil: predicciones más recientes con datos del producto
-- ============================================================
CREATE OR REPLACE VIEW v_pronosticos_completos AS
SELECT
    p.item,
    d.nombre_item,
    d.nombre_linea_n1,
    d.nombre_linea_n2,
    p.centro_operacion,
    p.fecha_inicio_semana,
    p.modelo,
    p.prediccion,
    p.limite_inferior,
    p.limite_superior,
    c.clase_abc,
    c.clase_xyz,
    c.segmento_abc_xyz,
    p.created_at
FROM pronosticos p
LEFT JOIN dim_producto d ON p.item = d.item
LEFT JOIN clasificacion_abc_xyz c ON p.item = c.item;
