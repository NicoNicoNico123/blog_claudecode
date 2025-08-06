import os
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'financial_blog'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password'),
            'sslmode': os.getenv('DB_SSLMODE', 'prefer')
        }
        self.engine = None
        
    def create_sqlalchemy_engine(self):
        """Create SQLAlchemy engine for ORM usage"""
        connection_string = f"postgresql://{self.connection_params['user']}:{self.connection_params['password']}@{self.connection_params['host']}:{self.connection_params['port']}/{self.connection_params['database']}"
        
        self.engine = create_engine(
            connection_string,
            poolclass=StaticPool,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={
                'sslmode': self.connection_params['sslmode'],
                'application_name': 'financial_blog_pipeline'
            }
        )
        return self.engine
    
    @contextmanager
    def get_raw_connection(self):
        """Get raw psycopg2 connection for advanced operations"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Get cursor with automatic cleanup"""
        with self.get_raw_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Database operation error: {e}")
                raise
            finally:
                cursor.close()
    
    def test_connection(self):
        """Test database connectivity"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                result = cursor.fetchone()
                logger.info(f"Database connection successful: {result}")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a single query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_transaction(self, queries):
        """Execute multiple queries in a transaction"""
        with self.get_raw_connection() as conn:
            cursor = conn.cursor()
            try:
                results = []
                for query, params in queries:
                    cursor.execute(query, params)
                    if query.strip().upper().startswith(('SELECT', 'INSERT', 'UPDATE')):
                        results.append(cursor.fetchall() if cursor.description else cursor.rowcount)
                conn.commit()
                return results
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
            finally:
                cursor.close()

# Global database connection instance
db = DatabaseConnection()

# Environment-specific configurations
class ZeaburConfig:
    """Configuration for Zeabur deployment"""
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')  # Provided by Zeabur
        self.connection_pool_size = int(os.getenv('DB_POOL_SIZE', '20'))
        self.max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '30'))
    
    def get_connection_string(self):
        return self.database_url or "postgresql://localhost/financial_blog"

# Connection health check
async def check_database_health():
    """Async health check for the database"""
    try:
        with db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            return {"status": "healthy", "timestamp": cursor.fetchone()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}