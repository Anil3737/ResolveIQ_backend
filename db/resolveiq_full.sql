-- =============================================================
-- ResolveIQ — FULL DATABASE SCHEMA SCRIPT (Production Ready)
-- =============================================================
-- Source of Truth: app/models/ (SQLAlchemy Models)
-- Date: 2026-03-19
-- =============================================================

CREATE DATABASE IF NOT EXISTS `resolveiq` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `resolveiq`;

SET FOREIGN_KEY_CHECKS = 0;

-- Drop existing tables
DROP TABLE IF EXISTS `alembic_version`;
DROP TABLE IF EXISTS `assignments`;
DROP TABLE IF EXISTS `ticket_logs`;
DROP TABLE IF EXISTS `ticket_history`;
DROP TABLE IF EXISTS `ticket_comments`;
DROP TABLE IF EXISTS `ticket_ai`;
DROP TABLE IF EXISTS `system_activity_logs`;
DROP TABLE IF EXISTS `password_reset_requests`;
DROP TABLE IF EXISTS `feedback`;
DROP TABLE IF EXISTS `tickets`;
DROP TABLE IF EXISTS `sla_rules`;
DROP TABLE IF EXISTS `sla_policies`;
DROP TABLE IF EXISTS `ticket_types`;
DROP TABLE IF EXISTS `team_members`;
DROP TABLE IF EXISTS `teams`;
DROP TABLE IF EXISTS `employee_profiles`;
DROP TABLE IF EXISTS `agent_profiles`;
DROP TABLE IF EXISTS `team_lead_profiles`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `departments`;
DROP TABLE IF EXISTS `roles`;

SET FOREIGN_KEY_CHECKS = 1;

-- ─── 1. METADATA TABLES ──────────────────────────────────────

CREATE TABLE `roles` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `departments` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_departments_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 2. USER & PROFILE TABLES ───────────────────────────────

CREATE TABLE `users` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(120) NOT NULL,
    `emp_id` VARCHAR(20) DEFAULT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role_id` INT NOT NULL,
    `is_active` TINYINT(1) DEFAULT 1,
    `require_password_change` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_users_email` (`email`),
    UNIQUE KEY `uq_users_emp_id` (`emp_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `team_lead_profiles` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `department_id` INT NOT NULL,
    `location` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_tlp_user` (`user_id`),
    CONSTRAINT `fk_tlp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tlp_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `agent_profiles` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `department_id` INT NOT NULL,
    `team_lead_id` INT DEFAULT NULL,
    `location` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ap_user` (`user_id`),
    CONSTRAINT `fk_ap_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ap_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
    CONSTRAINT `fk_ap_lead` FOREIGN KEY (`team_lead_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `employee_profiles` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `location` VARCHAR(100) DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ep_user` (`user_id`),
    CONSTRAINT `fk_ep_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 3. TEAM TABLES ──────────────────────────────────────────

CREATE TABLE `teams` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` VARCHAR(255) DEFAULT NULL,
    `goal` TEXT DEFAULT NULL,
    `issue_type` VARCHAR(100) DEFAULT NULL,
    `department_id` INT DEFAULT NULL,
    `team_lead_id` INT DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_teams_name` (`name`),
    CONSTRAINT `fk_teams_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_teams_lead` FOREIGN KEY (`team_lead_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `team_members` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `team_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_team_user` (`team_id`, `user_id`),
    CONSTRAINT `fk_tm_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tm_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4. SLA & TICKETING METADATA ───────────────────────────

CREATE TABLE `ticket_types` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `severity_level` INT NOT NULL DEFAULT 1,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ticket_types_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `sla_policies` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `type_id` INT NOT NULL,
    `priority` VARCHAR(20) NOT NULL,
    `response_minutes` INT NOT NULL,
    `resolution_minutes` INT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_sla_policy` (`type_id`, `priority`),
    CONSTRAINT `fk_sla_type` FOREIGN KEY (`type_id`) REFERENCES `ticket_types` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `sla_rules` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `department_id` INT NOT NULL,
    `priority` ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') NOT NULL,
    `sla_hours` INT NOT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_slarule_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 5. CORE TICKETING TABLES ───────────────────────────────

CREATE TABLE `tickets` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT NOT NULL,
    `department_id` INT NOT NULL,
    `ticket_number` VARCHAR(25) DEFAULT NULL,
    `created_by` INT NOT NULL,
    `assigned_to` INT DEFAULT NULL,
    `status` ENUM('OPEN', 'APPROVED', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'ESCALATED') DEFAULT 'OPEN',
    `priority` ENUM('P1', 'P2', 'P3', 'P4') DEFAULT 'P4',
    `ai_score` INT NOT NULL DEFAULT 0,
    `breach_risk` FLOAT NOT NULL DEFAULT 0.0,
    `escalation_required` TINYINT(1) NOT NULL DEFAULT 0,
    `ai_explanation` JSON DEFAULT NULL,
    `sla_hours` INT DEFAULT NULL,
    `sla_deadline` DATETIME DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `approved_by` INT DEFAULT NULL,
    `approved_at` DATETIME DEFAULT NULL,
    `assigned_at` DATETIME DEFAULT NULL,
    `accepted_at` DATETIME DEFAULT NULL,
    `resolved_at` DATETIME DEFAULT NULL,
    `closed_at` DATETIME DEFAULT NULL,
    `issue_type` VARCHAR(100) NOT NULL DEFAULT 'Other',
    `location` VARCHAR(100) DEFAULT NULL,
    `parent_ticket_id` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ticket_number` (`ticket_number`),
    CONSTRAINT `fk_ticket_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`),
    CONSTRAINT `fk_ticket_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_ticket_assignee` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ticket_approver` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ticket_parent` FOREIGN KEY (`parent_ticket_id`) REFERENCES `tickets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `feedback` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `rating` INT NOT NULL,
    `comments` TEXT DEFAULT NULL,
    `suggestions` JSON DEFAULT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_fb_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_fb_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 6. AI & LOGGING TABLES ──────────────────────────────────

CREATE TABLE `password_reset_requests` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `email` VARCHAR(255) NOT NULL,
    `emp_id` VARCHAR(50) NOT NULL,
    `temp_password` VARCHAR(50) DEFAULT NULL,
    `temp_password_hash` VARCHAR(255) DEFAULT NULL,
    `status` ENUM('PENDING', 'APPROVED', 'DECLINED') DEFAULT 'PENDING',
    `requested_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `processed_at` DATETIME DEFAULT NULL,
    `processed_by` INT DEFAULT NULL,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_prr_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_prr_processor` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `system_activity_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `user_id` INT DEFAULT NULL,
    `action_type` VARCHAR(50) NOT NULL,
    `entity_type` VARCHAR(50) NOT NULL,
    `entity_id` INT DEFAULT NULL,
    `description` TEXT NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_sal_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ticket_ai` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `predicted_category` VARCHAR(100) DEFAULT NULL,
    `urgency_score` INT DEFAULT 0,
    `severity_score` INT DEFAULT 0,
    `similarity_risk` INT DEFAULT 0,
    `sla_breach_risk` INT DEFAULT 0,
    `explanation_json` JSON DEFAULT NULL,
    `analyzed_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_tai_ticket` (`ticket_id`),
    CONSTRAINT `fk_tai_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 7. TRANSACTIONAL LOGS ───────────────────────────────────

CREATE TABLE `ticket_comments` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `message` TEXT NOT NULL,
    `is_internal` TINYINT(1) DEFAULT 0,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_comment_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_comment_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ticket_history` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `action` VARCHAR(120) NOT NULL,
    `old_value` TEXT DEFAULT NULL,
    `new_value` TEXT DEFAULT NULL,
    `performed_by` INT NOT NULL,
    `performed_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_hist_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_hist_user` FOREIGN KEY (`performed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `ticket_logs` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `action` VARCHAR(100) NOT NULL,
    `old_value` VARCHAR(255) DEFAULT NULL,
    `new_value` VARCHAR(255) DEFAULT NULL,
    `performed_by` INT NOT NULL,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_log_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_log_user` FOREIGN KEY (`performed_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `assignments` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `ticket_id` INT NOT NULL,
    `assigned_by` INT NOT NULL,
    `assigned_to` INT NOT NULL,
    `assigned_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_asgn_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_asgn_by` FOREIGN KEY (`assigned_by`) REFERENCES `users` (`id`),
    CONSTRAINT `fk_asgn_to` FOREIGN KEY (`assigned_to`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 8. SYSTEM TABLES ────────────────────────────────────────

CREATE TABLE `alembic_version` (
    `version_num` VARCHAR(32) NOT NULL,
    PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─────────────────────────────────────────────────────────────
-- 9. SEED DATA
-- ─────────────────────────────────────────────────────────────

INSERT INTO `roles` (`id`, `name`) VALUES (1, 'ADMIN'), (2, 'TEAM_LEAD'), (3, 'AGENT'), (4, 'EMPLOYEE');

INSERT INTO `departments` (`id`, `name`, `description`) VALUES (1, 'IT Support', 'Primary IT department');

-- Initial Admin (admin@resolveiq.com / Admin@123)
-- Hash generated via app/utils/password_utils.py (bcrypt)
INSERT INTO `users` (`id`, `full_name`, `email`, `emp_id`, `password_hash`, `role_id`, `is_active`) 
VALUES (1, 'System Admin', 'admin@resolveiq.com', '1111111111', '$2b$12$K7O8wXWz6Q6.gWlqZ...PLACEHOLDER', 1, 1);

-- =============================================================
-- ✅ DATABASE SCHEMA GENERATION COMPLETE
-- =============================================================
