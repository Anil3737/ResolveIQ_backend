-- =============================================================
-- ResolveIQ — FULL DATABASE RECOVERY SCRIPT
-- =============================================================
-- Purpose : Fix MySQL #1932 errors after XAMPP reinstall
-- Database: resolveiq
-- Engine  : InnoDB
-- Date    : 2026-02-18
-- =============================================================
-- HOW TO RUN:
--   Option A — phpMyAdmin: Open SQL tab → paste → Execute
--   Option B — CLI:
--     cd C:\xampp\mysql\bin
--     mysql -u root < "C:\Users\DELL\OneDrive\Desktop\resolveiq_backend\db\resolveiq_full_recovery.sql"
-- =============================================================

-- ─────────────────────────────────────────────────────────────
-- 0. USE / CREATE DATABASE
-- ─────────────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS `resolveiq`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE `resolveiq`;

-- ─────────────────────────────────────────────────────────────
-- 1. DISABLE FK CHECKS (required for clean drop order)
-- ─────────────────────────────────────────────────────────────
SET FOREIGN_KEY_CHECKS = 0;

-- ─────────────────────────────────────────────────────────────
-- 2. DROP ALL TABLES (child → parent order)
-- ─────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS `alembic_version`;
DROP TABLE IF EXISTS `ticket_ai`;
DROP TABLE IF EXISTS `ticket_history`;
DROP TABLE IF EXISTS `ticket_logs`;
DROP TABLE IF EXISTS `ticket_comments`;
DROP TABLE IF EXISTS `assignments`;
DROP TABLE IF EXISTS `audit_logs`;
DROP TABLE IF EXISTS `sla_policies`;
DROP TABLE IF EXISTS `sla_rules`;
DROP TABLE IF EXISTS `team_members`;
DROP TABLE IF EXISTS `teams`;
DROP TABLE IF EXISTS `ticket_types`;
DROP TABLE IF EXISTS `tickets`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `departments`;
DROP TABLE IF EXISTS `roles`;

-- ─────────────────────────────────────────────────────────────
-- 3. RE-ENABLE FK CHECKS
-- ─────────────────────────────────────────────────────────────
SET FOREIGN_KEY_CHECKS = 1;


-- =============================================================
-- 4. CREATE TABLES  (parent → child order)
-- =============================================================

-- ─── 4.1 ROLES ──────────────────────────────────────────────
CREATE TABLE `roles` (
    `id`   INT          NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50)  NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_roles_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.2 DEPARTMENTS ────────────────────────────────────────
CREATE TABLE `departments` (
    `id`   INT          NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_departments_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.3 USERS ──────────────────────────────────────────────
CREATE TABLE `users` (
    `id`            INT          NOT NULL AUTO_INCREMENT,
    `full_name`     VARCHAR(100) NOT NULL,
    `email`         VARCHAR(120) NOT NULL,
    `phone`         VARCHAR(20)  DEFAULT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role_id`       INT          NOT NULL DEFAULT 4,
    `department_id` INT          DEFAULT NULL,
    `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_users_email` (`email`),
    KEY `ix_users_role` (`role_id`),
    KEY `ix_users_dept` (`department_id`),
    CONSTRAINT `fk_users_role`       FOREIGN KEY (`role_id`)       REFERENCES `roles`(`id`),
    CONSTRAINT `fk_users_department` FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.4 TICKET_TYPES ───────────────────────────────────────
CREATE TABLE `ticket_types` (
    `id`             INT          NOT NULL AUTO_INCREMENT,
    `name`           VARCHAR(100) NOT NULL,
    `severity_level` INT          NOT NULL DEFAULT 1,
    `created_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ticket_types_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.5 TICKETS ────────────────────────────────────────────
CREATE TABLE `tickets` (
    `id`                  INT                                                       NOT NULL AUTO_INCREMENT,
    `title`               VARCHAR(200)                                              NOT NULL,
    `description`         TEXT                                                      NOT NULL,
    `department_id`       INT                                                       NOT NULL,
    `created_by`          INT                                                       NOT NULL,
    `assigned_to`         INT                                                       DEFAULT NULL,
    `status`              ENUM('OPEN','IN_PROGRESS','RESOLVED','CLOSED','ESCALATED') NOT NULL DEFAULT 'OPEN',
    `priority`            ENUM('P1','P2','P3','P4')                                  NOT NULL DEFAULT 'P4',
    `ai_score`            INT                                                       NOT NULL DEFAULT 0,
    `breach_risk`         FLOAT                                                     NOT NULL DEFAULT 0.0,
    `escalation_required` TINYINT(1)                                                NOT NULL DEFAULT 0,
    `sla_hours`           INT                                                       DEFAULT NULL,
    `sla_deadline`        DATETIME                                                  DEFAULT NULL,
    `created_at`          DATETIME                                                  DEFAULT CURRENT_TIMESTAMP,
    `updated_at`          DATETIME                                                  DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `resolved_at`         DATETIME                                                  DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_tickets_dept`       (`department_id`),
    KEY `ix_tickets_created_by` (`created_by`),
    KEY `ix_tickets_assigned`   (`assigned_to`),
    CONSTRAINT `fk_tickets_department` FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`),
    CONSTRAINT `fk_tickets_created_by` FOREIGN KEY (`created_by`)   REFERENCES `users`(`id`),
    CONSTRAINT `fk_tickets_assigned`   FOREIGN KEY (`assigned_to`)  REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.6 AUDIT_LOGS ────────────────────────────────────────
CREATE TABLE `audit_logs` (
    `id`           INT          NOT NULL AUTO_INCREMENT,
    `action`       VARCHAR(255) NOT NULL,
    `performed_by` INT          NOT NULL,
    `ticket_id`    INT          DEFAULT NULL,
    `timestamp`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_audit_user`   (`performed_by`),
    KEY `ix_audit_ticket` (`ticket_id`),
    CONSTRAINT `fk_audit_user`   FOREIGN KEY (`performed_by`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_audit_ticket` FOREIGN KEY (`ticket_id`)    REFERENCES `tickets`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.7 TEAMS ──────────────────────────────────────────────
CREATE TABLE `teams` (
    `id`            INT          NOT NULL AUTO_INCREMENT,
    `name`          VARCHAR(100) NOT NULL,
    `description`   VARCHAR(255) DEFAULT NULL,
    `department_id` INT          DEFAULT NULL,
    `team_lead_id`  INT          DEFAULT NULL,
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_teams_name` (`name`),
    KEY `ix_teams_dept` (`department_id`),
    KEY `ix_teams_lead` (`team_lead_id`),
    CONSTRAINT `fk_teams_department` FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`),
    CONSTRAINT `fk_teams_lead`       FOREIGN KEY (`team_lead_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.8 TEAM_MEMBERS ──────────────────────────────────────
CREATE TABLE `team_members` (
    `id`         INT      NOT NULL AUTO_INCREMENT,
    `team_id`    INT      NOT NULL,
    `user_id`    INT      NOT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_team_user` (`team_id`, `user_id`),
    KEY `ix_tm_user` (`user_id`),
    CONSTRAINT `fk_tm_team` FOREIGN KEY (`team_id`) REFERENCES `teams`(`id`),
    CONSTRAINT `fk_tm_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.9 ASSIGNMENTS ───────────────────────────────────────
CREATE TABLE `assignments` (
    `id`          INT      NOT NULL AUTO_INCREMENT,
    `ticket_id`   INT      NOT NULL,
    `assigned_by` INT      NOT NULL,
    `assigned_to` INT      NOT NULL,
    `assigned_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_assign_ticket` (`ticket_id`),
    KEY `ix_assign_by`     (`assigned_by`),
    KEY `ix_assign_to`     (`assigned_to`),
    CONSTRAINT `fk_assign_ticket` FOREIGN KEY (`ticket_id`)   REFERENCES `tickets`(`id`),
    CONSTRAINT `fk_assign_by`     FOREIGN KEY (`assigned_by`) REFERENCES `users`(`id`),
    CONSTRAINT `fk_assign_to`     FOREIGN KEY (`assigned_to`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.10 SLA_POLICIES ─────────────────────────────────────
CREATE TABLE `sla_policies` (
    `id`                 INT         NOT NULL AUTO_INCREMENT,
    `type_id`            INT         NOT NULL,
    `priority`           VARCHAR(20) NOT NULL,
    `response_minutes`   INT         NOT NULL,
    `resolution_minutes` INT         NOT NULL,
    `created_at`         DATETIME    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_sla_ticket_type_priority` (`type_id`, `priority`),
    CONSTRAINT `fk_sla_policy_type` FOREIGN KEY (`type_id`) REFERENCES `ticket_types`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.11 SLA_RULES ────────────────────────────────────────
CREATE TABLE `sla_rules` (
    `id`            INT                                     NOT NULL AUTO_INCREMENT,
    `department_id` INT                                     NOT NULL,
    `priority`      ENUM('LOW','MEDIUM','HIGH','CRITICAL')  NOT NULL,
    `sla_hours`     INT                                     NOT NULL,
    PRIMARY KEY (`id`),
    KEY `ix_sla_rules_dept` (`department_id`),
    CONSTRAINT `fk_sla_rules_dept` FOREIGN KEY (`department_id`) REFERENCES `departments`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.12 TICKET_COMMENTS ──────────────────────────────────
CREATE TABLE `ticket_comments` (
    `id`          INT        NOT NULL AUTO_INCREMENT,
    `ticket_id`   INT        NOT NULL,
    `user_id`     INT        NOT NULL,
    `message`     TEXT       NOT NULL,
    `is_internal` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at`  DATETIME   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_tc_ticket` (`ticket_id`),
    KEY `ix_tc_user`   (`user_id`),
    CONSTRAINT `fk_tc_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets`(`id`),
    CONSTRAINT `fk_tc_user`   FOREIGN KEY (`user_id`)   REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.13 TICKET_LOGS ──────────────────────────────────────
CREATE TABLE `ticket_logs` (
    `id`           INT          NOT NULL AUTO_INCREMENT,
    `ticket_id`    INT          NOT NULL,
    `action`       VARCHAR(100) NOT NULL,
    `old_value`    VARCHAR(255) DEFAULT NULL,
    `new_value`    VARCHAR(255) DEFAULT NULL,
    `performed_by` INT          NOT NULL,
    `timestamp`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_tl_ticket` (`ticket_id`),
    KEY `ix_tl_user`   (`performed_by`),
    CONSTRAINT `fk_tl_ticket` FOREIGN KEY (`ticket_id`)    REFERENCES `tickets`(`id`),
    CONSTRAINT `fk_tl_user`   FOREIGN KEY (`performed_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.14 TICKET_HISTORY ───────────────────────────────────
CREATE TABLE `ticket_history` (
    `id`           INT          NOT NULL AUTO_INCREMENT,
    `ticket_id`    INT          NOT NULL,
    `action`       VARCHAR(120) NOT NULL,
    `old_value`    TEXT         DEFAULT NULL,
    `new_value`    TEXT         DEFAULT NULL,
    `performed_by` INT          NOT NULL,
    `performed_at` DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_th_ticket` (`ticket_id`),
    KEY `ix_th_user`   (`performed_by`),
    CONSTRAINT `fk_th_ticket` FOREIGN KEY (`ticket_id`)    REFERENCES `tickets`(`id`),
    CONSTRAINT `fk_th_user`   FOREIGN KEY (`performed_by`) REFERENCES `users`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.15 TICKET_AI ────────────────────────────────────────
CREATE TABLE `ticket_ai` (
    `id`                 INT          NOT NULL AUTO_INCREMENT,
    `ticket_id`          INT          NOT NULL,
    `predicted_category` VARCHAR(100) DEFAULT NULL,
    `urgency_score`      INT          NOT NULL DEFAULT 0,
    `severity_score`     INT          NOT NULL DEFAULT 0,
    `similarity_risk`    INT          NOT NULL DEFAULT 0,
    `sla_breach_risk`    INT          NOT NULL DEFAULT 0,
    `explanation_json`   JSON         DEFAULT NULL,
    `analyzed_at`        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ticket_ai_ticket` (`ticket_id`),
    CONSTRAINT `fk_tai_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets`(`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ─── 4.16 ALEMBIC_VERSION ──────────────────────────────────
CREATE TABLE `alembic_version` (
    `version_num` VARCHAR(32) NOT NULL,
    PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- =============================================================
-- 5. SEED DATA
-- =============================================================

-- ─── 5.1 ROLES ──────────────────────────────────────────────
INSERT INTO `roles` (`id`, `name`) VALUES
    (1, 'ADMIN'),
    (2, 'TEAM_LEAD'),
    (3, 'AGENT'),
    (4, 'EMPLOYEE');

-- ─── 5.2 DEPARTMENTS ────────────────────────────────────────
INSERT INTO `departments` (`id`, `name`) VALUES
    (1, 'IT Support');

-- ─── 5.3 ADMIN USER ─────────────────────────────────────────
-- Password: admin123  (werkzeug scrypt hash)
-- Generated via: generate_password_hash('admin123')
INSERT INTO `users` (`id`, `full_name`, `email`, `phone`, `password_hash`, `role_id`, `department_id`, `is_active`)
VALUES (
    1,
    'Admin User',
    'admin@resolveiq.com',
    '9999999999',
    'scrypt:32768:8:1$salt$placeholder',   -- ← Replace with real hash (see note below)
    1,
    1,
    1
);
-- ┌──────────────────────────────────────────────────────────┐
-- │  IMPORTANT: The password_hash above is a PLACEHOLDER.   │
-- │  Run the Python command below AFTER this SQL to set      │
-- │  the real password:                                      │
-- │                                                          │
-- │  cd C:\Users\DELL\OneDrive\Desktop\resolveiq_backend     │
-- │  python -c "                                             │
-- │  from app import create_app                              │
-- │  from app.extensions import db                           │
-- │  from app.models.user import User                        │
-- │  app = create_app()                                      │
-- │  with app.app_context():                                 │
-- │      u = User.query.get(1)                               │
-- │      u.set_password('admin123')                          │
-- │      db.session.commit()                                 │
-- │      print('Admin password set!')                        │
-- │  "                                                       │
-- └──────────────────────────────────────────────────────────┘


-- =============================================================
-- 6. VERIFICATION QUERIES
-- =============================================================

-- Check all tables exist
SELECT TABLE_NAME, ENGINE, TABLE_ROWS
FROM   INFORMATION_SCHEMA.TABLES
WHERE  TABLE_SCHEMA = 'resolveiq'
ORDER  BY TABLE_NAME;

-- Check foreign key constraints
SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM   INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE  TABLE_SCHEMA = 'resolveiq'
  AND  REFERENCED_TABLE_NAME IS NOT NULL
ORDER  BY TABLE_NAME, CONSTRAINT_NAME;

-- Verify seed data
SELECT 'roles'       AS tbl, COUNT(*) AS cnt FROM `roles`
UNION ALL
SELECT 'departments' AS tbl, COUNT(*) AS cnt FROM `departments`
UNION ALL
SELECT 'users'       AS tbl, COUNT(*) AS cnt FROM `users`;

-- Quick smoke test: try creating/deleting a ticket
-- (Uncomment to run)
-- INSERT INTO tickets (title, description, department_id, created_by)
--     VALUES ('Test Ticket', 'Smoke test', 1, 1);
-- SELECT * FROM tickets;
-- DELETE FROM tickets WHERE title = 'Test Ticket';

SELECT '✅ ALL TABLES CREATED SUCCESSFULLY' AS result;
