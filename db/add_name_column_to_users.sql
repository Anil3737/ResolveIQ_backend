-- Add 'name' column to users table if it does not exist
ALTER TABLE users ADD COLUMN name VARCHAR(100) NOT NULL AFTER id;