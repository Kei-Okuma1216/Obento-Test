-- init.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
);

INSERT INTO users (name, email) VALUES
('Taro', 'taro@example.com'),
('Hanako', 'hanako@example.com');

-- SELECT * FROM public.users;

-- データの挿入
-- INSERT INTO users (name, email) VALUES ('Kei Okuma', 'kei.okuma@gmail.com');

