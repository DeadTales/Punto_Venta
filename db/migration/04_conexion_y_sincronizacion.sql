-- Ejecutar DESPUÉS de 01_tablas_iniciales.sql en una base existente.
-- Revisar y respaldar antes. Esta migración no se aplica al arrancar la API.
BEGIN;
ALTER TABLE categoria ADD COLUMN IF NOT EXISTS sync_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE cliente ADD COLUMN IF NOT EXISTS sync_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE empleado ADD COLUMN IF NOT EXISTS sync_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE producto ADD COLUMN IF NOT EXISTS sync_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE venta ADD COLUMN IF NOT EXISTS sync_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE venta ADD COLUMN IF NOT EXISTS request_hash VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS uq_categoria_sync_id ON categoria(sync_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_cliente_sync_id ON cliente(sync_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_empleado_sync_id ON empleado(sync_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_producto_sync_id ON producto(sync_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_venta_sync_id ON venta(sync_id);

CREATE TABLE IF NOT EXISTS sync_outbox (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    kind VARCHAR(50) NOT NULL,
    payload JSON NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'conflict')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_sync_outbox_status ON sync_outbox(status);
CREATE TABLE IF NOT EXISTS sync_receipt (
    event_id UUID PRIMARY KEY,
    payload_hash VARCHAR(64) NOT NULL,
    received_at TIMESTAMP NOT NULL DEFAULT NOW()
);
COMMIT;
