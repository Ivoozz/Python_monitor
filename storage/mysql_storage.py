#!/usr/bin/env python3
"""
MySQL Storage for Metrics
Stores metrics in MySQL database
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading


class MySQLStorage:
    """Storage implementation using MySQL database"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize MySQL storage"""
        self.config = config
        self.logger = logging.getLogger('MySQLStorage')
        
        # Database configuration
        self.db_config = {
            'host': config.get('mysql_host', 'localhost'),
            'port': config.get('mysql_port', 3306),
            'user': config.get('mysql_user', 'monitor'),
            'password': config.get('mysql_password', ''),
            'database': config.get('mysql_database', 'monitoring'),
            'charset': 'utf8mb4'
        }
        
        self.connection = None
        self._lock = threading.Lock()
        
        # Try to connect, if fails, log warning
        try:
            self._connect()
            self.logger.info("MySQL storage initialized successfully")
        except Exception as e:
            self.logger.warning(f"MySQL connection failed: {e}. Falling back to file storage.")
            # Fall back to file storage
            from file_storage import FileStorage
            self._fallback_storage = FileStorage(config)
            self._use_fallback = True
        else:
            self._use_fallback = False
    
    def _connect(self):
        """Establish database connection"""
        import pymysql
        self.connection = pymysql.connect(**self.db_config)
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure the metrics table exists"""
        if self._use_fallback:
            return
        
        create_table_sql = """
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
            INDEX idx_agent_time (agent_name, collection_time),
            INDEX idx_collection_time (collection_time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
            self.connection.commit()
        except Exception as e:
            self.logger.error(f"Error creating table: {e}")
            raise
    
    def store(self, metrics_list: List[Dict[str, Any]]):
        """Store metrics to database"""
        if self._use_fallback:
            self._fallback_storage.store(metrics_list)
            return
        
        with self._lock:
            try:
                # Ensure connection is alive
                if not self.connection or not self.connection.open:
                    self._connect()
                
                with self.connection.cursor() as cursor:
                    for metrics in metrics_list:
                        self._store_single_metric(cursor, metrics)
                
                self.connection.commit()
                self.logger.info(f"Stored {len(metrics_list)} metrics to MySQL")
                
            except Exception as e:
                self.logger.error(f"Error storing to MySQL: {e}")
                # Try fallback storage
                try:
                    self._fallback_storage.store(metrics_list)
                except:
                    pass
    
    def _store_single_metric(self, cursor, metrics: Dict[str, Any]):
        """Store a single metric to the database"""
        if metrics.get('status') == 'error':
            # Store error information
            sql = """
            INSERT INTO metrics (agent_name, collection_time, cpu_usage, security_status, raw_data)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                metrics.get('agent_name', 'unknown'),
                metrics.get('collection_time', datetime.now().isoformat()),
                -1,  # Indicate error
                'ERROR',
                json.dumps(metrics, default=str)
            ))
            return
        
        # Extract metrics
        cpu_temp = metrics.get('cpu_temperature')
        cpu_usage = metrics.get('cpu_usage', 0)
        
        system_load = metrics.get('system_load', {})
        load_1min = system_load.get('1min', 0)
        load_5min = system_load.get('5min', 0)
        load_15min = system_load.get('15min', 0)
        
        memory = metrics.get('memory_usage', {})
        mem_total = memory.get('total', 0)
        mem_used = memory.get('used', 0)
        mem_percent = memory.get('percent', 0)
        
        disk = metrics.get('disk_usage', {})
        disk_total = disk.get('total', 0)
        disk_used = disk.get('used', 0)
        disk_percent = disk.get('percent', 0)
        
        security = metrics.get('security_threats', {})
        sec_status = security.get('status', 'UNKNOWN')
        sec_issues = json.dumps(security.get('issues', []))
        
        alerts = json.dumps(metrics.get('alerts', []))
        
        sql = """
        INSERT INTO metrics (
            agent_name, collection_time,
            cpu_temperature, cpu_usage,
            system_load_1min, system_load_5min, system_load_15min,
            memory_total, memory_used, memory_percent,
            disk_total, disk_used, disk_percent,
            security_status, security_issues,
            alerts, raw_data
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        
        cursor.execute(sql, (
            metrics.get('agent_name', 'unknown'),
            metrics.get('collection_time', datetime.now().isoformat()),
            cpu_temp,
            cpu_usage,
            load_1min, load_5min, load_15min,
            mem_total, mem_used, mem_percent,
            disk_total, disk_used, disk_percent,
            sec_status, sec_issues,
            alerts,
            json.dumps(metrics, default=str)
        ))
    
    def query(self, agent_name: str = None, start_time: str = None, 
              end_time: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Query stored metrics"""
        if self._use_fallback:
            return self._fallback_storage.query(agent_name, start_time, end_time)
        
        results = []
        
        try:
            if not self.connection or not self.connection.open:
                self._connect()
            
            # Build query
            sql = "SELECT * FROM metrics WHERE 1=1"
            params = []
            
            if agent_name:
                sql += " AND agent_name = %s"
                params.append(agent_name)
            
            if start_time:
                sql += " AND collection_time >= %s"
                params.append(start_time)
            
            if end_time:
                sql += " AND collection_time <= %s"
                params.append(end_time)
            
            sql += " ORDER BY collection_time DESC LIMIT %s"
            params.append(limit)
            
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                columns = [col[0] for col in cursor.description]
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
            
        except Exception as e:
            self.logger.error(f"Error querying MySQL: {e}")
        
        return results
    
    def get_agent_names(self) -> List[str]:
        """Get list of all agent names"""
        if self._use_fallback:
            return []
        
        try:
            if not self.connection or not self.connection.open:
                self._connect()
            
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT DISTINCT agent_name FROM metrics ORDER BY agent_name")
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error getting agent names: {e}")
            return []
    
    def get_latest_metrics(self, agent_name: str = None) -> List[Dict[str, Any]]:
        """Get latest metrics for each agent"""
        if self._use_fallback:
            return self._fallback_storage.query(agent_name)
        
        results = []
        
        try:
            if not self.connection or not self.connection.open:
                self._connect()
            
            if agent_name:
                sql = """
                SELECT * FROM metrics 
                WHERE agent_name = %s 
                ORDER BY collection_time DESC 
                LIMIT 1
                """
                with self.connection.cursor() as cursor:
                    cursor.execute(sql, (agent_name,))
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
            else:
                # Get latest for each agent
                sql = """
                SELECT m1.* FROM metrics m1
                INNER JOIN (
                    SELECT agent_name, MAX(collection_time) as max_time
                    FROM metrics
                    GROUP BY agent_name
                ) m2 ON m1.agent_name = m2.agent_name AND m1.collection_time = m2.max_time
                """
                with self.connection.cursor() as cursor:
                    cursor.execute(sql)
                    columns = [col[0] for col in cursor.description]
                    for row in cursor.fetchall():
                        results.append(dict(zip(columns, row)))
            
        except Exception as e:
            self.logger.error(f"Error getting latest metrics: {e}")
        
        return results
    
    def close(self):
        """Close database connection"""
        if hasattr(self, '_fallback_storage'):
            self._fallback_storage.close()
        
        if self.connection:
            self.connection.close()
            self.logger.info("MySQL connection closed")
