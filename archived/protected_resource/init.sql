-- Create the database if it doesn't exist
CREATE DATABASE protected_resource;

-- Connect to the database
\c protected_resource;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create students table
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone_number VARCHAR(20),
    highest_education VARCHAR(255),
    sgpa FLOAT,
    cgpa FLOAT,
    hostel_id INTEGER,
    room_number VARCHAR(20),
    sharing_type VARCHAR(50)
);

-- Create teachers table
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(255),
    specialization VARCHAR(255)
);

-- Create hostels table
CREATE TABLE IF NOT EXISTS hostels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    capacity INTEGER,
    warden_id INTEGER
);

-- Insert test data
INSERT INTO users (email, username, hashed_password, role) VALUES
    ('admin@example.com', 'admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'admin'),
    ('teacher@example.com', 'teacher', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'teacher'),
    ('warden@example.com', 'warden', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'warden');

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE protected_resource TO protected_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO protected_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO protected_user; 