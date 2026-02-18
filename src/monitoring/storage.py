"""
Storage abstraction layer for the monitoring system.
Supports both file-based logging and MySQL database storage.
"""

import os
import json
import logging
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    def save_metric(self, agent_name: str, metric_type: str, value: Any, 
                    timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None) -> bool:
        """Save a metric to storage."""
        pass

    @abstractmethod
    def get_metrics(self, agent_name: str, metric_type: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics from storage."""
        pass

    @abstractmethod
    def get_agents(self) -> List[str]:
        """Get list of all known agents."""
        pass

    @abstractmethod
    def close(self):
        """Close any open connections."""
        pass


class LogStorage(StorageBackend):
    """File-based storage using JSON lines with rotation support."""

    def __init__(self, log_dir: str = None):
        # Use fallback path if /var/log is not writable
        if log_dir is None:
            log_dir = os.environ.get('MONITORING_DATA_DIR')
            if log_dir is None:
                # Try /var/log/monitoring/data first, fallback to ./data
                for candidate in ['/var/log/monitoring/data', './data']:
                    try:
                        Path(candidate).mkdir(parents=True, exist_ok=True)
                        # Test if writable
                        test_file = Path(candidate) / '.test'
                        test_file.touch()
                        test_file.unlink()
                        log_dir = candidate
                        break
                    except (PermissionError, OSError):
                        continue
        
        self.log_dir = Path(log_dir)
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to current directory
            self.log_dir = Path('./data')
            self.log_dir.mkdir(parents=True, exist_ok=True)
            logging.warning(f"Using fallback data directory: {self.log_dir}")
        
        self.log_file = self.log_dir / "metrics.jsonl"
        self._lock = threading.Lock()

    def save_metric(self, agent_name: str, metric_type: str, value: Any,
                    timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None) -> bool:
        """Save metric to JSONL file."""
        with self._lock:
            try:
                entry = {
                    "timestamp": (timestamp or datetime.now()).isoformat(),
                    "agent": agent_name,
                    "metric_type": metric_type,
                    "value": value,
                    "metadata": metadata or {}
                }
                with open(self.log_file, "a") as f:
                    f.write(json.dumps(entry) + "\n")
                return True
            except Exception as e:
                logging.error(f"Failed to save metric to log: {e}")
                return False

    def get_metrics(self, agent_name: str, metric_type: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics from JSONL file."""
        results = []
        if not self.log_file.exists():
            return results

        with self._lock:
            try:
                with open(self.log_file, "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get("agent") != agent_name:
                                continue
                            if metric_type and entry.get("metric_type") != metric_type:
                                continue

                            entry_time = datetime.fromisoformat(entry.get("timestamp", ""))
                            if start_time and entry_time < start_time:
                                continue
                            if end_time and entry_time > end_time:
                                continue

                            results.append(entry)
                        except (json.JSONDecodeError, ValueError):
                            continue
            except Exception as e:
                logging.error(f"Failed to read metrics from log: {e}")

        return results

    def get_agents(self) -> List[str]:
        """Get list of all known agents from log file."""
        agents = set()
        if not self.log_file.exists():
            return []

        with self._lock:
            try:
                with open(self.log_file, "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if "agent" in entry:
                                agents.add(entry["agent"])
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logging.error(f"Failed to get agents from log: {e}")

        return sorted(list(agents))

    def close(self):
        """Close connections (no-op for file storage)."""
        pass


class MySQLStorage(StorageBackend):
    """MySQL database storage backend."""

    def __init__(self, host: str = "localhost", port: int = 3306,
                 user: str = "monitor", password: str = "changeme",
                 database: str = "monitoring"):
        self.config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database
        }
        self._connection = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self):
        """Establish database connection."""
        try:
            import pymysql
            self._connection = pymysql.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )
            logging.info("Connected to MySQL database")
        except ImportError:
            logging.error("pymysql not installed. Install with: pip install pymysql")
            raise
        except Exception as e:
            logging.error(f"Failed to connect to MySQL: {e}")
            raise

    def save_metric(self, agent_name: str, metric_type: str, value: Any,
                    timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None) -> bool:
        """Save metric to MySQL database."""
        with self._lock:
            try:
                if self._connection is None:
                    self._connect()

                cursor = self._connection.cursor()
                sql = """INSERT INTO metrics (agent_name, metric_type, value, metadata, timestamp)
                         VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(sql, (
                    agent_name,
                    metric_type,
                    str(value),
                    json.dumps(metadata or {}),
                    timestamp or datetime.now()
                ))
                self._connection.commit()
                cursor.close()
                return True
            except Exception as e:
                logging.error(f"Failed to save metric to MySQL: {e}")
                return False

    def get_metrics(self, agent_name: str, metric_type: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics from MySQL database."""
        results = []
        with self._lock:
            try:
                if self._connection is None:
                    self._connect()

                cursor = self._connection.cursor()
                sql = "SELECT * FROM metrics WHERE agent_name = %s"
                params = [agent_name]

                if metric_type:
                    sql += " AND metric_type = %s"
                    params.append(metric_type)

                if start_time:
                    sql += " AND timestamp >= %s"
                    params.append(start_time)

                if end_time:
                    sql += " AND timestamp <= %s"
                    params.append(end_time)

                sql += " ORDER BY timestamp DESC"

                cursor.execute(sql, params)
                results = cursor.fetchall()
                cursor.close()
            except Exception as e:
                logging.error(f"Failed to get metrics from MySQL: {e}")

        return results

    def get_agents(self) -> List[str]:
        """Get list of all known agents from database."""
        agents = []
        with self._lock:
            try:
                if self._connection is None:
                    self._connect()

                cursor = self._connection.cursor()
                cursor.execute("SELECT DISTINCT agent_name FROM metrics ORDER BY agent_name")
                agents = [row["agent_name"] for row in cursor.fetchall()]
                cursor.close()
            except Exception as e:
                logging.error(f"Failed to get agents from MySQL: {e}")

        return agents

    def close(self):
        """Close database connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None


class SQLiteStorage(StorageBackend):
    """SQLite database storage backend (fallback when MySQL unavailable)."""

    def __init__(self, db_path: str = None):
        # Use fallback path if /var/log is not writable
        if db_path is None:
            db_path = os.environ.get('MONITORING_DB_PATH')
            if db_path is None:
                # Try /var/log/monitoring/metrics.db first, fallback to ./metrics.db
                for candidate in ['/var/log/monitoring/metrics.db', './metrics.db']:
                    try:
                        Path(candidate).parent.mkdir(parents=True, exist_ok=True)
                        # Test if writable
                        test_file = Path(candidate).parent / '.test'
                        test_file.touch()
                        test_file.unlink()
                        db_path = candidate
                        break
                    except (PermissionError, OSError):
                        continue
        
        self.db_path = Path(db_path) if db_path else Path('./metrics.db')
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            self.db_path = Path('./metrics.db')
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            logging.warning(f"Using fallback database path: {self.db_path}")
        
        self._connection = None
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        with self._lock:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
            cursor = self._connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_name TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_metric_time 
                ON metrics(agent_name, metric_type, timestamp)
            """)
            self._connection.commit()
            cursor.close()

    def save_metric(self, agent_name: str, metric_type: str, value: Any,
                    timestamp: Optional[datetime] = None, metadata: Optional[Dict] = None) -> bool:
        """Save metric to SQLite database."""
        with self._lock:
            try:
                cursor = self._connection.cursor()
                sql = """INSERT INTO metrics (agent_name, metric_type, value, metadata, timestamp)
                         VALUES (?, ?, ?, ?, ?)"""
                cursor.execute(sql, (
                    agent_name,
                    metric_type,
                    str(value),
                    json.dumps(metadata or {}),
                    timestamp or datetime.now()
                ))
                self._connection.commit()
                cursor.close()
                return True
            except Exception as e:
                logging.error(f"Failed to save metric to SQLite: {e}")
                return False

    def get_metrics(self, agent_name: str, metric_type: Optional[str] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[Dict]:
        """Retrieve metrics from SQLite database."""
        results = []
        with self._lock:
            try:
                cursor = self._connection.cursor()
                sql = "SELECT * FROM metrics WHERE agent_name = ?"
                params = [agent_name]

                if metric_type:
                    sql += " AND metric_type = ?"
                    params.append(metric_type)

                if start_time:
                    sql += " AND timestamp >= ?"
                    params.append(start_time)

                if end_time:
                    sql += " AND timestamp <= ?"
                    params.append(end_time)

                sql += " ORDER BY timestamp DESC"

                cursor.execute(sql, params)
                results = [dict(row) for row in cursor.fetchall()]
                cursor.close()
            except Exception as e:
                logging.error(f"Failed to get metrics from SQLite: {e}")

        return results

    def get_agents(self) -> List[str]:
        """Get list of all known agents from database."""
        agents = []
        with self._lock:
            try:
                cursor = self._connection.cursor()
                cursor.execute("SELECT DISTINCT agent_name FROM metrics ORDER BY agent_name")
                agents = [row[0] for row in cursor.fetchall()]
                cursor.close()
            except Exception as e:
                logging.error(f"Failed to get agents from SQLite: {e}")

        return agents

    def close(self):
        """Close database connection."""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None


def create_storage(backend: str = "log", **kwargs) -> StorageBackend:
    """Factory function to create storage backend."""
    if backend == "mysql":
        return MySQLStorage(**kwargs)
    elif backend == "sqlite":
        return SQLiteStorage(**kwargs)
    else:
        return LogStorage(**kwargs)
