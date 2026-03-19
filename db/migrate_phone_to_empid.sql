-- Migration: Rename phone to emp_id in users table
-- Run this in your MySQL console/workbench to fix the "Unknown column 'users.emp_id'" error.

USE resolveiq_db; -- Change this if your database name is different

ALTER TABLE users 
CHANGE COLUMN phone emp_id VARCHAR(20) DEFAULT NULL;

-- Also update the unique index name for clarity
ALTER TABLE users 
DROP INDEX uq_users_phone,
ADD UNIQUE INDEX uq_users_emp_id (emp_id);
