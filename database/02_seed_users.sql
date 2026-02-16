-- =====================================
-- SEED - USUÁRIO ADMIN
-- =====================================
INSERT INTO core.users (name, email, password_hash, role)
VALUES (
    'Juliano Saroba',
    'admin@jsp.com',
    crypt('123456', gen_salt('bf')),
    'admin'
)
ON CONFLICT (email) DO NOTHING;

-- =====================================
-- SEED - OUTROS USUÁRIOS
-- =====================================
INSERT INTO core.users (name, email, password_hash, role)
VALUES
('Tecnico 1', 'tec1@jsp.com', crypt('123456', gen_salt('bf')), 'technician'),
('Financeiro 1', 'fin@jsp.com', crypt('123456', gen_salt('bf')), 'finance')
ON CONFLICT (email) DO NOTHING;
