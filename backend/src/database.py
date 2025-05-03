import mysql.connector
from dotenv import load_dotenv
import os
from mysql.connector.pooling import MySQLConnectionPool

load_dotenv()

pool = MySQLConnectionPool(
    pool_name="mypool",
    pool_size=20,                  # Increase from 10
    pool_reset_session=True,
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    connection_timeout=30,         # Add timeout
    autocommit=True                # Ensure autocommit is on
)

class Database:
    def __init__(self):
        self.conn = pool.get_connection()
        self.cursor = self.conn.cursor(dictionary=True)
        self._create_tables()
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def _create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                doc_id VARCHAR(255) UNIQUE,
                title VARCHAR(255),
                workspace_name VARCHAR(255),
                timestamp VARCHAR(255),
                content_path TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_manager (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(255),
                workspace_name VARCHAR(255) UNIQUE,
                total_files INT DEFAULT 0,
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_files (
                id INT AUTO_INCREMENT PRIMARY KEY,
                workspace_id INT,
                file_name VARCHAR(255),
                file_path VARCHAR(255),
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspace_manager(id) ON DELETE CASCADE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_files_docID (
                id INT AUTO_INCREMENT PRIMARY KEY,
                workspace_id INT,
                file_id INT,
                doc_id VARCHAR(255),
                last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workspace_id) REFERENCES workspace_manager(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES workspace_files(id) ON DELETE CASCADE
            )
        """)

        # Create trigger for file insertion
        self.cursor.execute("""
            DROP TRIGGER IF EXISTS after_workspace_file_insert
        """)

        self.cursor.execute("""
            CREATE TRIGGER after_workspace_file_insert
            AFTER INSERT ON workspace_files
            FOR EACH ROW
            BEGIN
                UPDATE workspace_manager 
                SET 
                    total_files = total_files + 1,
                    last_modified = CURRENT_TIMESTAMP
                WHERE id = NEW.workspace_id;
            END
        """)

        # Create trigger for file deletion
        self.cursor.execute("""
            DROP TRIGGER IF EXISTS after_workspace_file_delete
        """)

        self.cursor.execute("""
            CREATE TRIGGER after_workspace_file_delete
            AFTER DELETE ON workspace_files
            FOR EACH ROW
            BEGIN
                UPDATE workspace_manager 
                SET 
                    total_files = total_files - 1,
                    last_modified = CURRENT_TIMESTAMP
                WHERE id = OLD.workspace_id;
            END
        """)

        self.conn.commit()

    def insert_document(self, doc_id, title,workspace_name, timestamp, content_path):
        query = """
            INSERT INTO documents (doc_id, title,workspace_name, timestamp, content_path)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.cursor.execute(query, (doc_id, title,workspace_name, timestamp, content_path))
        self.conn.commit()
        print(f"doc_id {doc_id} added into db of title {title}")

    def get_contentPath_fromDocument(self, doc_id):
        """Get content path for a document by its doc_id"""
        try:
            if not doc_id:
                print(f"Warning: Empty doc_id passed to get_contentPath_fromDocument")
                return None
                
            self.cursor.execute(
                "SELECT content_path FROM documents WHERE doc_id=%s",
                (doc_id,)
            )
            result = self.cursor.fetchone()
            
            # Debug information
            if not result:
                print(f"No content path in db found with doc_id: {doc_id}")
                return None
                
            # Since your cursor uses dictionary=True, use key access instead of index
            return result['content_path'] if result else None
        except Exception as e:
            print(f"Database error in get_contentPath_fromDocument: {str(e)}")
            print(f"Type of doc_id: {type(doc_id)}, Value: {doc_id}")
            return None

    def delete_doc(self, doc_id):
        """
        Delete a document from the database by its doc_id.
        
        Args:
            doc_id (str): The document ID to delete
            
        Returns:
            bool: True if document was deleted successfully, False otherwise
            
        Raises:
            ValueError: If doc_id is None or empty
        """
        if not doc_id:
            print(f"Error: Empty doc_id passed to delete_doc")
            return False
        
        try:
            # First check if document exists
            self.cursor.execute("SELECT id FROM documents WHERE doc_id = %s", (doc_id,))
            result = self.cursor.fetchone()
            
            if not result:
                print(f"Warning: No document found with doc_id: {doc_id}")
                return False
            
            # Delete the document
            query = "DELETE FROM documents WHERE doc_id = %s"
            self.cursor.execute(query, (doc_id,))
            rows_affected = self.cursor.rowcount
            self.conn.commit()
            
            print(f"Successfully deleted document with doc_id: {doc_id}, rows affected: {rows_affected}")
            return rows_affected > 0
            
        except Exception as e:
            print(f"Database error in delete_doc: {str(e)}")
            # Rollback in case of error
            try:
                self.conn.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {str(rollback_error)}")
            return False

    def create_workspace(self, user_id, workspace_name):
        """Create a new workspace"""
        try:
            query = """
                INSERT INTO workspace_manager (user_id, workspace_name)
                VALUES (%s, %s)
            """
            self.cursor.execute(query, (user_id, workspace_name))
            self.conn.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry error
                self.cursor.execute("SELECT id FROM workspace_manager WHERE workspace_name = %s", (workspace_name,))
                result = self.cursor.fetchone()
                return result[0] if result else None
            raise

    def add_file_to_workspace(self, workspace_id, file_name, file_path):
        """Add a file to a workspace"""
        query = """
            INSERT INTO workspace_files (workspace_id, file_name, file_path)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (workspace_id, file_name, file_path))
        self.conn.commit()
        return self.cursor.lastrowid


    def get_workspace_details_by_id(self, workspace_id):
        """Get detailed workspace information by name"""
        try:
            # Create a new cursor with dictionary=True
            cursor = self.conn.cursor(dictionary=True)
            
            # Query without date formatting - fetch raw timestamps
            query = """
                SELECT id, workspace_name, user_id, total_files, 
                    last_modified, created_at
                FROM workspace_manager
                WHERE id = %s
            """
            
            cursor.execute(query, [workspace_id])
            result = cursor.fetchone()
            cursor.close()
            
            # If we have results, format the dates in Python
            if result:
                # Convert MySQL datetime objects to formatted strings
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return result
        except Exception as e:
            print(f"Database error in get_workspace_details: {str(e)}")
            return None

    def get_all_workspaces(self):
        """Get all workspaces with formatted dates"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, workspace_name, user_id, total_files, 
                    last_modified, created_at
                FROM workspace_manager
                ORDER BY last_modified DESC
            """)
            results = cursor.fetchall()
            
            # Format dates in Python
            for result in results:
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return results
        except Exception as e:
            print(f"Database error in get_all_workspaces: {str(e)}")
            return None

    def get_workspace_details(self, workspace_name):
        """Get detailed workspace information by name"""
        try:
            # Create a new cursor with dictionary=True
            cursor = self.conn.cursor(dictionary=True)
            
            # Query without date formatting - fetch raw timestamps
            query = """
                SELECT id, workspace_name, user_id, total_files, 
                    last_modified, created_at
                FROM workspace_manager
                WHERE workspace_name = %s
            """
            
            cursor.execute(query, [workspace_name])
            result = cursor.fetchone()
            cursor.close()
            
            # If we have results, format the dates in Python
            if result:
                # Convert MySQL datetime objects to formatted strings
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return result
        except Exception as e:
            print(f"Database error in get_workspace_details: {str(e)}")
            print(f"Query attempted with parameter: '{workspace_name}'")
            return None
        
    def get_workspace_files_detailed(self, workspace_id):
        """Get all files in a workspace with formatted dates"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            
            # Remove DATE_FORMAT from SQL - fetch raw timestamps instead
            cursor.execute("""
                SELECT id, file_name, last_modified, created_at
                FROM workspace_files
                WHERE workspace_id = %s
                ORDER BY last_modified DESC
            """, (workspace_id,))
            
            results = cursor.fetchall()
            
            # Format dates in Python instead of MySQL
            for result in results:
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return results
        except Exception as e:
            print(f"Database error in get_workspace_files_detailed: {str(e)}")
            return None

    def check_file_exists_in_workspace(self, workspace_id, file_name):
        """Check if a file already exists in the workspace"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id FROM workspace_files 
                WHERE workspace_id = %s AND file_name = %s
            """, (workspace_id, file_name))
            result = cursor.fetchone()
            return result is not None, result[0] if result else None
        except Exception as e:
            print(f"Database error in check_file_exists_in_workspace: {str(e)}")
            return False, None

    def delete_workspace(self, workspace_id):
        """Delete a workspace (cascade will handle files)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM workspace_manager WHERE id = %s", (workspace_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error in delete_workspace: {str(e)}")
            self.conn.rollback()
            return False
        
    def delete_workspace_file(self, file_id):
        """Delete a workspace (cascade will handle files)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM workspace_files WHERE id = %s", (file_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Database error in delete_workspace: {str(e)}")
            self.conn.rollback()
            return False

    def get_workspace_by_name(self, workspace_name):
        """Get detailed workspace information by name"""
        try:
            # Create a new cursor with dictionary=True
            cursor = self.conn.cursor(dictionary=True)
            
            # Query without date formatting - fetch raw timestamps
            query = """
                SELECT id, workspace_name, user_id, total_files, 
                    last_modified, created_at
                FROM workspace_manager
                WHERE workspace_name = %s
            """
            
            cursor.execute(query, [workspace_name])
            result = cursor.fetchone()
            cursor.close()
            
            # If we have results, format the dates in Python
            if result:
                # Convert MySQL datetime objects to formatted strings
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return result
        except Exception as e:
            print(f"Database error in get_workspace_details: {str(e)}")
            print(f"Query attempted with parameter: '{workspace_name}'")
            return None

    def get_file_details(self, file_id):
        """Get detailed file information by ID"""
        try:
            cursor = self.conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, file_name, file_path, last_modified, created_at
                FROM workspace_files
                WHERE id = %s
            """, (file_id,))
            result = cursor.fetchone()
            
            # Format dates in Python instead of MySQL
            if result:
                if result['last_modified']:
                    result['last_modified'] = result['last_modified'].strftime('%Y-%m-%d %H:%M:%S')
                if result['created_at']:
                    result['created_at'] = result['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return result
        except Exception as e:
            print(f"Database error in get_file_details: {str(e)}")
            return None

    def add_workspace_file_docID(self, workspace_id, file_id, doc_id):
        """
        Insert a new record into workspace_files_docID.
        """
        query = """
            INSERT INTO workspace_files_docID (workspace_id, file_id, doc_id)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (workspace_id, file_id, doc_id))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_workspace_file_docIDs(self, workspace_id=None, file_id=None):
        """
        Select records from workspace_files_docID.
        If workspace_id or file_id is provided, filter by those columns.
        """
        base_query = "SELECT doc_id FROM workspace_files_docID"
        conditions = []
        params = []
        
        if workspace_id is not None:
            conditions.append("workspace_id = %s")
            params.append(workspace_id)
        if file_id is not None:
            conditions.append("file_id = %s")
            params.append(file_id)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
            
        self.cursor.execute(base_query, tuple(params))
        results = self.cursor.fetchall()
        return results

    def delete_workspace_file_docID(self, doc_id):
        """
        Delete a record from workspace_files_docID by its doc_id.
        """
        query = "DELETE FROM workspace_files_docID WHERE doc_id = %s"
        self.cursor.execute(query, (doc_id,))
        self.conn.commit()
        return self.cursor.rowcount

if __name__ == "__main__":
    database = Database()
    print(f"Testing database functions...")
    
    result=database.delete_workspace_file()
    print(f"Result: {result}")