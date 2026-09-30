1 PASO CREACION DEL ENTORNO VIRTUAL 
----python -m venv venv ---------
=============================

2 activar el entorno virtual 
venv/Script/activate

================================
3 istalacion de la librerias que se esta usando en el proyecto en general y que funcione nada mas 
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
bcrypt
python-jose[cryptography]
pydantic
pydantic-settings
python-multipart

codigo para istalar todo de las librerias 
---------pip install fastapi uvicorn[standard] sqlalchemy psycopg2-binary bcrypt python-jose[cryptography] pydantic pydantic-settings python-multipart-----------
===================================================

4 nombre de la base de datos en como se llama /proyecto01

select *from users
select *from orders
select *from order_items
select *from products


-- 1. Tabla de Usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabla de Productos
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    image_url VARCHAR(255) NOT NULL
);

-- 3. Tabla de Pedidos / Órdenes
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Tabla de Detalle de Pedidos
CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DOUBLE PRECISION NOT NULL
);

-- 5. Insertar productos iniciales (si aún no existen)
INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Detergente Líquido 1L', 'aseo', 3.50, 20, 'https://images.unsplash.com/photo-1585421514738-01798e348b17?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Detergente Líquido 1L');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Jabón Antibacterial 3 Pack', 'aseo', 2.20, 35, 'https://images.unsplash.com/photo-1607006314143-6c8411b7d5ca?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Jabón Antibacterial 3 Pack');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Limpia Pisos Lavanda 750ml', 'aseo', 1.80, 15, 'https://images.unsplash.com/photo-1563453392212-326f5e854473?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Limpia Pisos Lavanda 750ml');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Pechuga de Pollo 1kg', 'carnes', 4.20, 18, 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Pechuga de Pollo 1kg');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Lomo de Res Fresco 1kg', 'carnes', 7.50, 12, 'https://images.unsplash.com/photo-1558030006-450675393462?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Lomo de Res Fresco 1kg');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Chuleta de Cerdo 1kg', 'carnes', 5.10, 10, 'https://images.unsplash.com/photo-1432139555190-58524dae6a55?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Chuleta de Cerdo 1kg');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Tomate Riñón 1kg', 'vegetales', 1.10, 40, 'https://images.unsplash.com/photo-1592924357228-91a4daadcfea?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Tomate Riñón 1kg');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Zanahoria Criolla 1kg', 'vegetales', 0.85, 50, 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Zanahoria Criolla 1kg');

INSERT INTO products (name, category, price, stock, image_url)
SELECT 'Lechuga Crespa x Unidad', 'vegetales', 0.60, 25, 'https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=300'
WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = 'Lechuga Crespa x Unidad');

-- Agregar columna de administrador si no existe
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- Marcar o crear el usuario admin
-- Si ya tienes un usuario creado o quieres crear 'admin' con clave 'admin123':
UPDATE users SET is_admin = TRUE WHERE username = 'admin';

-- Eliminar el admin previo desactualizado si existe
DELETE FROM users WHERE username = 'admin';

============================================
5 ejecutar el programa con uvicorn

-------------uvicorn app.main:app --reload --port 8000-------------------

