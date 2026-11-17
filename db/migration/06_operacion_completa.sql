-- Ejecutar después de 04 y 05. Cambios aditivos; no elimina información.
ALTER TABLE empleado ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE empleado ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS turno_caja (
    id_turno SERIAL PRIMARY KEY,
    operation_id UUID NOT NULL UNIQUE,
    request_hash VARCHAR(64) NOT NULL,
    id_empleado INTEGER NOT NULL REFERENCES empleado(id_empleado),
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('Abierta', 'Cerrada')),
    apertura TIMESTAMP NOT NULL DEFAULT NOW(),
    cierre TIMESTAMP,
    fondo_inicial NUMERIC(10,2) NOT NULL CHECK (fondo_inicial >= 0),
    efectivo_esperado NUMERIC(10,2),
    efectivo_contado NUMERIC(10,2) CHECK (efectivo_contado >= 0),
    diferencia NUMERIC(10,2),
    close_operation_id UUID UNIQUE,
    close_hash VARCHAR(64),
    notas VARCHAR(500)
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_turno_empleado_abierto
    ON turno_caja(id_empleado) WHERE estado = 'Abierta';

ALTER TABLE venta ADD COLUMN IF NOT EXISTS id_turno INTEGER REFERENCES turno_caja(id_turno);
ALTER TABLE venta ADD COLUMN IF NOT EXISTS tasa_impuesto NUMERIC(5,4) NOT NULL DEFAULT 0;
ALTER TABLE venta ADD COLUMN IF NOT EXISTS subtotal NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE venta ADD COLUMN IF NOT EXISTS impuesto NUMERIC(10,2) NOT NULL DEFAULT 0;
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cancel_operation_id UUID UNIQUE;
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cancel_hash VARCHAR(64);
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cancel_motivo VARCHAR(250);
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cancelado_por INTEGER REFERENCES empleado(id_empleado);
ALTER TABLE venta ADD COLUMN IF NOT EXISTS cancelado_en TIMESTAMP;
UPDATE venta SET subtotal = total WHERE subtotal = 0 AND impuesto = 0 AND total > 0;
ALTER TABLE detalle_venta ADD COLUMN IF NOT EXISTS nombre_producto VARCHAR(150);
ALTER TABLE detalle_venta ADD COLUMN IF NOT EXISTS codigo_barras VARCHAR(50);
