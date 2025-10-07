import sqlite3
import os
import json
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_path='stress_data.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(50) PRIMARY KEY,
                username VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Stress records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stress_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(50) NOT NULL,
                stress_score DECIMAL(3,1) NOT NULL,
                stress_level VARCHAR(15) NOT NULL,
                input_method VARCHAR(20) NOT NULL,
                explanation TEXT,
                analysis_metadata TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_timestamp ON stress_records(user_id, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON stress_records(timestamp)')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def save_stress_record(self, user_id, record_data):
        """Save stress analysis record"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update or insert user
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, last_activity)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id,
                record_data.get('username', 'Unknown')
            ))
            
            # Prepare analysis metadata
            analysis_metadata = json.dumps(record_data.get('analysis_metadata', {}))
            
            # Save stress record
            cursor.execute('''
                INSERT INTO stress_records 
                (user_id, stress_score, stress_level, input_method, explanation, analysis_metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                record_data['stress_score'],
                record_data['stress_level'],
                record_data['input_method'],
                record_data.get('explanation', '')[:1000],  # Limit length
                analysis_metadata
            ))
            
            conn.commit()
            print(f"✅ Record saved for user {user_id} - Score: {record_data['stress_score']}")
            
        except Exception as e:
            print(f"❌ Error saving record: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def get_user_history(self, user_id, limit=50):
        """Get user's stress history"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT stress_score, stress_level, input_method, explanation, analysis_metadata, timestamp
                FROM stress_records 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            records = cursor.fetchall()
            
            formatted_records = []
            for record in records:
                try:
                    analysis_metadata = json.loads(record[4]) if record[4] else {}
                except:
                    analysis_metadata = {}
                
                formatted_records.append({
                    'stress_score': float(record[0]),
                    'stress_level': record[1],
                    'input_method': record[2],
                    'explanation': record[3],
                    'analysis_metadata': analysis_metadata,
                    'timestamp': record[5]
                })
            
            print(f"📊 Retrieved {len(formatted_records)} records for user {user_id}")
            return formatted_records
            
        except Exception as e:
            print(f"❌ Error getting user history: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_database_stats(self):
        """Get database statistics"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM stress_records')
            total_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Get recent activity
            cursor.execute('''
                SELECT COUNT(*) FROM stress_records 
                WHERE timestamp > datetime('now', '-7 days')
            ''')
            recent_records = cursor.fetchone()[0]
            
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            
            return {
                'total_records': total_records,
                'total_users': total_users,
                'recent_records_7d': recent_records,
                'database_size_mb': round(size_mb, 2)
            }
        except Exception as e:
            print(f"❌ Error getting database stats: {e}")
            return {}
        finally:
            if conn:
                conn.close()
    
    def auto_cleanup(self):
        """Clean up old records"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete records older than 90 days
            cursor.execute('''
                DELETE FROM stress_records 
                WHERE timestamp < datetime('now', '-90 days')
            ''')
            
            deleted_count = cursor.rowcount
            
            # Delete users with no records
            cursor.execute('''
                DELETE FROM users 
                WHERE user_id NOT IN (SELECT DISTINCT user_id FROM stress_records)
            ''')
            
            deleted_users = cursor.rowcount
            
            conn.commit()
            
            print(f"🗑️ Cleanup completed: {deleted_count} old records, {deleted_users} orphaned users removed")
            
            return {
                'deleted_records': deleted_count,
                'deleted_users': deleted_users
            }
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
            if conn:
                conn.rollback()
            return {}
        finally:
            if conn:
                conn.close()