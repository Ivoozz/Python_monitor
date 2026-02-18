-- MySQL Database Initialization for System Monitoring
-- Run this script to set up the database and user

-- Create database
CREATE DATABASE IF NOT EXISTS monitoring CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (change password as needed)
CREATE USER IF NOT EXISTS 'monitor'@'localhost' IDENTIFIED BY 'monitor_password';
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON monitoring.* TO 'monitor'@'localhost';
GRANT ALL PRIVILEGES ON monitoring.* TO 'monitor'@'%';
FLUSH PRIVILEGES;

-- Use the database
USE monitoring;

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    collection_time DATETIME NOT NULL,
    cpu_temperature FLOAT,
    cpu_usage FLOAT,
    system_load_1min FLOAT,
    system_load_5min FLOAT,
    system_load_15min FLOAT,
    memory_total FLOAT,
    memory_used FLOAT,
    memory_percent FLOAT,
    disk_total FLOAT,
    disk_used FLOAT,
    disk_percent FLOAT,
    security_status VARCHAR(50),
    security_issues TEXT,
    alerts TEXT,
    raw_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_time (agent_name, collection_time),
    INDEX idx_collection_time (collection_time),
    INDEX idx_agent_collection (agent_name, collection_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create alerts table for historical alert tracking
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    value FLOAT,
    threshold FLOAT,
    collection_time DATETIME NOT NULL,
    resolved_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_time (agent_name, collection_time),
    INDEX idx_severity (severity),
    INDEX idx_type (alert_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create agent status table for tracking agent availability
CREATE TABLE IF NOT EXISTS agent_status (
    id INT AUTO_INCREMENT PRIMARY KEY,
    agent_name VARCHAR(255) UNIQUE NOT NULL,
    status ENUM('ONLINE', 'OFFLINE', 'ERROR') NOT NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    version VARCHAR(50),
    uptime_start TIMESTAMP NULL,
    total_metrics INT DEFAULT 0,
    total_alerts INT DEFAULT 0,
    INDEX idx_status (status),
    INDEX idx_last_seen (last_seen)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Create index for better query performance
CREATE INDEX idx_metrics_time_agent ON metrics(collection_time, agent_name);
CREATE INDEX idx_alerts_time_severity ON alerts(collection_time, severity);

-- Sample data for testing (optional)
-- You can comment this out if you don't want sample data

/*
INSERT INTO agent_status (agent_name, status, ip_address, version) VALUES
('localhost', 'ONLINE', '127.0.0.1', '1.0.0'),
('test-agent', 'ONLINE', '192.168.1.100', '1.0.0');
*/

-- Show created tables
SHOW TABLES;
