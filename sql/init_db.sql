-- MySQL Database Initialization Script for Monitoring System
-- Run this script to set up the MySQL database

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS monitoring 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE monitoring;

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    value TEXT NOT NULL,
    metadata JSON,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_metric_type (metric_type),
    INDEX idx_timestamp (timestamp),
    INDEX idx_agent_metric_time (agent_name, metric_type, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Alerts table for storing threshold violations
CREATE TABLE IF NOT EXISTS alerts (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity ENUM('info', 'warning', 'critical') NOT NULL,
    message TEXT NOT NULL,
    value DOUBLE,
    threshold DOUBLE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at DATETIME,
    acknowledged_by VARCHAR(255),
    INDEX idx_agent_name (agent_name),
    INDEX idx_severity (severity),
    INDEX idx_created_at (created_at),
    INDEX idx_ack (acknowledged, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Agents table for tracking monitored systems
CREATE TABLE IF NOT EXISTS agents (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    host VARCHAR(255) NOT NULL,
    port INT UNSIGNED NOT NULL,
    status ENUM('active', 'inactive', 'error') DEFAULT 'active',
    last_connected DATETIME,
    first_seen DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Security events table
CREATE TABLE IF NOT EXISTS security_events (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    description TEXT NOT NULL,
    details JSON,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_severity (severity),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System info table for agent snapshots
CREATE TABLE IF NOT EXISTS system_info (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    hostname VARCHAR(255),
    platform VARCHAR(100),
    platform_version VARCHAR(100),
    cpu_count INT,
    memory_total BIGINT,
    disk_total BIGINT,
    collected_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create user and grant privileges
-- Note: Run separately if you want to create a dedicated user
-- CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'changeme';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON monitoring.* TO 'monitor'@'%';
-- FLUSH PRIVILEGES;

-- View for latest metrics (useful for dashboards)
CREATE OR REPLACE VIEW latest_metrics AS
SELECT agent_name, metric_type, value, timestamp
FROM metrics m1
WHERE timestamp = (
    SELECT MAX(timestamp)
    FROM metrics m2
    WHERE m1.agent_name = m2.agent_name 
    AND m1.metric_type = m2.metric_type
);

-- View for active alerts
CREATE OR REPLACE VIEW active_alerts AS
SELECT * FROM alerts
WHERE acknowledged = FALSE
ORDER BY created_at DESC;

-- Procedure to clean old data
DELIMITER //
CREATE PROCEDURE IF NOT EXISTS cleanup_old_data(IN days_to_keep INT)
BEGIN
    DELETE FROM metrics WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    DELETE FROM alerts WHERE created_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    DELETE FROM security_events WHERE timestamp < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
    DELETE FROM system_info WHERE collected_at < DATE_SUB(NOW(), INTERVAL days_to_keep DAY);
END //
DELIMITER ;

-- Example: Run cleanup for data older than 30 days
-- CALL cleanup_old_data(30);
