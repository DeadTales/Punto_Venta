INSERT INTO METODO_PAGO (nombre) VALUES 
('Efectivo'),
('Tarjeta Débito'),
('Tarjeta Crédito'),
('Transferencia')
ON CONFLICT DO NOTHING;


INSERT INTO CATEGORIA (nombre, descripcion) VALUES 
('General', 'Artículos generales y misceláneos')
ON CONFLICT DO NOTHING;


INSERT INTO EMPLEADO (nombre, apellido, correo, password_hash, rol, telefono) VALUES 
(
    'Administrador', 
    'Principal', 
    'admin@pos.com', 
    '$2a$10$GfK33lR0.hU7t7c6R553e.2hR3r9Jz8h2nN2f3e8b0hW5zU0t7Pqm', 
    'Administrador', 
    '3300000000'
)
ON CONFLICT (correo) DO NOTHING;