-- Create Database
CREATE DATABASE IF NOT EXISTS resolveiq_db;

-- Create User and Grant Privileges
-- This is for local XAMPP development
-- You can change 'root'@'localhost' if needed, but here is a specific user creation if required
-- CREATE USER 'resolveiq_user'@'localhost' IDENTIFIED BY 'resolveiq_pass';
-- GRANT ALL PRIVILEGES ON resolveiq_db.* TO 'resolveiq_user'@'localhost';
-- FLUSH PRIVILEGES;

USE resolveiq_db;

-- Departments Seed
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT IGNORE INTO departments (name) VALUES 
('Engineering'), 
('HR'), 
('Finance'), 
('Sales & Marketing'), 
('Customer Support'), 
('Operations');
