-- Aplicar después de 04_conexion_y_sincronizacion.sql en bases existentes.
-- Conserva el historial y permite reintentar un ajuste con el mismo UUID.
CREATE TABLE IF NOT EXISTS ajuste_inventario (
    operation_id UUID PRIMARY KEY,
    id_producto INT NOT NULL REFERENCES producto(id_producto),
    id_empleado INT NOT NULL REFERENCES empleado(id_empleado),
    cantidad NUMERIC(10,3) NOT NULL CHECK (cantidad <> 0),
    stock_anterior NUMERIC(10,3) NOT NULL CHECK (stock_anterior >= 0),
    stock_nuevo NUMERIC(10,3) NOT NULL CHECK (stock_nuevo >= 0),
    motivo VARCHAR(250) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    fecha_hora TIMESTAMP NOT NULL DEFAULT NOW(),
    CHECK (stock_nuevo = stock_anterior + cantidad)
);
