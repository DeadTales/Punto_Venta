-- ========================================================
-- 1. EMPLEADOS ADICIONALES (CAJERO Y SUPERVISOR)
-- ========================================================
INSERT INTO EMPLEADO (nombre, apellido, correo, password_hash, rol, telefono) VALUES 
('Carlos', 'Ramírez', 'carlos.cajero@pos.com', '$2a$10$GfK33lR0.hU7t7c6R553e.2hR3r9Jz8h2nN2f3e8b0hW5zU0t7Pqm', 'Cajero', '3311223344'),
('María', 'Fernández', 'maria.supervisor@pos.com', '$2a$10$GfK33lR0.hU7t7c6R553e.2hR3r9Jz8h2nN2f3e8b0hW5zU0t7Pqm', 'Supervisor', '3355667788')
ON CONFLICT (correo) DO NOTHING;

-- ========================================================
-- 2. CATEGORÍAS DE PRODUCTOS
-- ========================================================
INSERT INTO CATEGORIA (nombre, descripcion) VALUES 
('Bebidas', 'Refrescos, aguas purificadas, jugos y energetizantes'),
('Snacks', 'Frituras, galletas y barras de cereal'),
('Farmacia', 'Medicamentos generales y primeros auxilios'),
('Abarrotes', 'Granos, enlatados, harinas y aceites')
ON CONFLICT DO NOTHING;

-- ========================================================
-- 3. CLIENTES REGISTRADOS
-- ========================================================
INSERT INTO CLIENTE (nombre, telefono, correo, rfc_o_identificacion_fiscal) VALUES 
('Abarrotes La Fe', '3399887766', 'contacto@abarroteslafe.com', 'ALF850101XYZ'),
('Lucía Mendoza Gómez', '3344556677', 'lucia.mendoza@gmail.com', 'MEL920304AA1'),
('Público General Mostrador', '3312345678', 'mostrador@tienda.com', NULL)
ON CONFLICT DO NOTHING;

-- ========================================================
-- 4. CATÁLOGO DE PRODUCTOS
-- ========================================================
INSERT INTO PRODUCTO (id_categoria, codigo_barras, nombre, descripcion, precio_compra, precio_venta, stock_actual, stock_minimo) VALUES 
(2, '7501055300075', 'Coca Cola 600ml', 'Refresco de cola PET no retornable', 12.50, 19.00, 50.000, 10.000),
(2, '7501000111223', 'Agua Natural Ciel 1L', 'Botella de agua purificada', 8.00, 14.50, 60.000, 15.000),
(3, '7501011115488', 'Papas Sabritas Sal 45g', 'Papas fritas con sal natural', 13.00, 21.50, 40.000, 10.000),
(3, '7501031311309', 'Galletas Emperador Chocolate 101g', 'Galletas sándwich con crema de chocolate', 11.20, 18.00, 30.000, 8.000),
(4, '7501234567890', 'Paracetamol 500mg 20 Tabletas', 'Caja de analgésico genérico', 15.00, 32.00, 25.000, 5.000),
(5, '7509998881112', 'Arroz Grano Grueso 1kg', 'Bolsa de arroz blanco de grano grueso', 21.00, 28.50, 35.500, 10.000)
ON CONFLICT (codigo_barras) DO NOTHING;

-- ========================================================
-- 5. HISTÓRICO DE TICKETS Y DETALLES DE VENTA
-- ========================================================
-- Venta 1: Cliente registrado, pagado en Efectivo (id_metodo_pago = 1), cobrado por Carlos (id_empleado = 2)
INSERT INTO VENTA (id_venta, id_cliente, id_empleado, id_metodo_pago, fecha_hora, total, estado) 
VALUES (1, 1, 2, 1, NOW() - INTERVAL '2 hours', 59.50, 'Completada');

INSERT INTO DETALLE_VENTA (id_venta, id_producto, cantidad, precio_unitario_venta, subtotal) VALUES 
(1, 1, 2.000, 19.00, 38.00), -- 2 Coca Colas
(1, 3, 1.000, 21.50, 21.50); -- 1 Papas Sabritas

-- Venta 2: Venta a mostrador (id_cliente = NULL), pagada con Tarjeta Débito (id_metodo_pago = 2)
INSERT INTO VENTA (id_venta, id_cliente, id_empleado, id_metodo_pago, fecha_hora, total, estado) 
VALUES (2, NULL, 2, 2, NOW() - INTERVAL '40 minutes', 50.00, 'Completada');

INSERT INTO DETALLE_VENTA (id_venta, id_producto, cantidad, precio_unitario_venta, subtotal) VALUES 
(2, 4, 1.000, 18.00, 18.00), -- 1 Galletas Emperador
(2, 5, 1.000, 32.00, 32.00); -- 1 Paracetamol

-- ========================================================
-- 6. SINCRONIZACIÓN DE SECUENCIAS SERIAL
-- Evita errores de clave duplicada en los siguientes inserts desde FastAPI
-- ========================================================
SELECT setval('categoria_id_categoria_seq', COALESCE((SELECT MAX(id_categoria) FROM CATEGORIA), 1));
SELECT setval('metodo_pago_id_metodo_pago_seq', COALESCE((SELECT MAX(id_metodo_pago) FROM METODO_PAGO), 1));
SELECT setval('empleado_id_empleado_seq', COALESCE((SELECT MAX(id_empleado) FROM EMPLEADO), 1));
SELECT setval('cliente_id_cliente_seq', COALESCE((SELECT MAX(id_cliente) FROM CLIENTE), 1));
SELECT setval('producto_id_producto_seq', COALESCE((SELECT MAX(id_producto) FROM PRODUCTO), 1));
SELECT setval('venta_id_venta_seq', COALESCE((SELECT MAX(id_venta) FROM VENTA), 1));
SELECT setval('detalle_venta_id_detalle_venta_seq', COALESCE((SELECT MAX(id_detalle_venta) FROM DETALLE_VENTA), 1));