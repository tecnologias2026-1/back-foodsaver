CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

INSERT INTO users (full_name, email)
VALUES
  ('Ana Torres', 'ana@example.com'),
  ('Luis Perez', 'luis@example.com')
ON CONFLICT (email) DO NOTHING;
