-- 1. Categorías de producto
CREATE TABLE IF NOT EXISTS CATEGORIA (
    id_categoria SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT
);

-- 2. Métodos de pago aceptados
CREATE TABLE IF NOT EXISTS METODO_PAGO (
    id_metodo_pago SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    CONSTRAINT chk_metodo_nombre CHECK (nombre IN ('Efectivo', 'Tarjeta Débito', 'Tarjeta Crédito', 'Transferencia'))
);

-- 3. Clientes (Registro de compradores)
CREATE TABLE IF NOT EXISTS CLIENTE (
    id_cliente SERIAL PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(150),
    rfc_o_identificacion_fiscal VARCHAR(50),
    CONSTRAINT chk_cliente_correo CHECK (correo LIKE '%@%')
);

-- 4. Empleados (Personal que opera el sistema y cajas)
CREATE TABLE IF NOT EXISTS EMPLEADO (
    id_empleado SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    correo VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(50) NOT NULL,
    telefono VARCHAR(20),
    CONSTRAINT chk_empleado_correo CHECK (correo LIKE '%@%'),
    CONSTRAINT chk_empleado_rol CHECK (rol IN ('Cajero', 'Administrador', 'Supervisor'))
);

-- 5. Productos (Artículos disponibles para venta)
CREATE TABLE IF NOT EXISTS PRODUCTO (
    id_producto SERIAL PRIMARY KEY,
    id_categoria INT NOT NULL,
    codigo_barras VARCHAR(50) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio_compra NUMERIC(10,2) NOT NULL,
    precio_venta NUMERIC(10,2) NOT NULL,
    stock_actual NUMERIC(10,3) NOT NULL,
    stock_minimo NUMERIC(10,3) NOT NULL,
    CONSTRAINT fk_producto_categoria FOREIGN KEY (id_categoria) REFERENCES CATEGORIA(id_categoria),
    CONSTRAINT chk_precio_compra CHECK (precio_compra >= 0),
    CONSTRAINT chk_precio_venta CHECK (precio_venta >= 0),
    CONSTRAINT chk_stock_actual CHECK (stock_actual >= 0),
    CONSTRAINT chk_stock_minimo CHECK (stock_minimo >= 0)
);

-- 6. Venta (Cabecera del ticket o transacción comercial)
CREATE TABLE IF NOT EXISTS VENTA (
    id_venta SERIAL PRIMARY KEY,
    id_cliente INT, 
    id_empleado INT NOT NULL,
    id_metodo_pago INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL DEFAULT NOW(),
    total NUMERIC(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    CONSTRAINT fk_venta_cliente FOREIGN KEY (id_cliente) REFERENCES CLIENTE(id_cliente),
    CONSTRAINT fk_venta_empleado FOREIGN KEY (id_empleado) REFERENCES EMPLEADO(id_empleado),
    CONSTRAINT fk_venta_metodo_pago FOREIGN KEY (id_metodo_pago) REFERENCES METODO_PAGO(id_metodo_pago),
    CONSTRAINT chk_venta_total CHECK (total >= 0),
    CONSTRAINT chk_venta_estado CHECK (estado IN ('Completada', 'Cancelada'))
);

-- 7. Detalle Venta (Renglones individuales del ticket - Relación N:M)
CREATE TABLE IF NOT EXISTS DETALLE_VENTA (
    id_detalle_venta SERIAL PRIMARY KEY,
    id_venta INT NOT NULL,
    id_producto INT NOT NULL,
    cantidad NUMERIC(10,3) NOT NULL,
    precio_unitario_venta NUMERIC(10,2) NOT NULL,
    subtotal NUMERIC(10,2) NOT NULL,
    CONSTRAINT fk_detalle_venta FOREIGN KEY (id_venta) REFERENCES VENTA(id_venta) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_producto FOREIGN KEY (id_producto) REFERENCES PRODUCTO(id_producto),
    CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_detalle_precio CHECK (precio_unitario_venta >= 0),
    CONSTRAINT chk_detalle_subtotal CHECK (subtotal >= 0)
);