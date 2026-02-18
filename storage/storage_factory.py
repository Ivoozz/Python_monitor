#!/usr/bin/env python3
"""
Storage Factory for Metric Collector
Creates storage instances based on configuration
"""

import logging
import os
import sys
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


class StorageFactory:
    """Factory for creating storage instances"""
    
    @staticmethod
    def create_storage(config: Dict[str, Any]):
        """Create a storage instance based on configuration"""
        storage_type = config.get('type', 'file').lower()
        
        if storage_type == 'mysql':
            from mysql_storage import MySQLStorage
            return MySQLStorage(config)
        elif storage_type == 'file' or storage_type == 'log':
            from file_storage import FileStorage
            return FileStorage(config)
        else:
            logger.warning(f"Unknown storage type: {storage_type}, using file storage")
            from file_storage import FileStorage
            return FileStorage(config)
