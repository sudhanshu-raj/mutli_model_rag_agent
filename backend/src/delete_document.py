"""
This contains all the method to delete either the whole workspace, or a single file from the workspace.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import vector_store as VS
import config as cfg
import json
import os
import stat
from logging_Setup import get_logger
import database 
logger=get_logger(__name__)

def get_db():
    return database.Database()


DOCS_METADATA_PATH = cfg.DOCS_METADATA_FILE
IMAGE_METADATA_PATH = cfg.IMAGES_METADATA_FILE
FILE_LIST=cfg.ALL_FILES_LIST
UPLOAD_DIR=cfg.UPLOAD_DIR
ALLOWED_IMAGE_EXTENSIONS=cfg.ALLWOED_IMAGE_EXTENSIONS

def delete_workspace_api(workspaceInfo):
    """
    Deletes an entire workspace along with all its associated file records sequentially.
    """
    db = None
    try:
        # Get fresh connection with timeout
        db = get_db()
        
        # Set a timeout for operations
        db.cursor.execute("SET SESSION wait_timeout=30")
        db.cursor.execute("SET SESSION interactive_timeout=30")
        
        workspace_id = workspaceInfo.get("id")
        workspace_name = workspaceInfo.get("workspace_name")
        if not workspace_id or not workspace_name:
            logger.error("Missing workspace id or workspace_name in workspaceInfo")
            return False

        # Log where we are
        logger.info(f"Starting deletion of workspace '{workspace_name}' (ID: {workspace_id})")
        
        # Get files but with a smaller transaction
        try:
            files = db.get_workspace_files_detailed(workspace_id)
            num_files = len(files) if files else 0
            logger.info(f"Found {num_files} file(s) in workspace '{workspace_name}'")
        except Exception as e:
            logger.error(f"Error getting files: {e}")
            return False
            
        # Delete each file individually with its own connection
        delete_results = []
        for idx, file in enumerate(files):
            logger.debug(f"Processing file {idx+1}/{num_files}")
            
            fileInfo = {
                "id": file["id"],
                "file_name": file["file_name"]
            }
            
            # Try with a timeout - don't let any single file hang the process
            try:
                logger.info(f"Starting deletion of file: {fileInfo['file_name']}")
                # Use a separate function with its own connection
                result = delete_file_api(workspaceInfo, fileInfo)
                delete_results.append(result)
                logger.info(f"Completed deletion of '{fileInfo['file_name']}', result: {result}")
            except Exception as ex:
                logger.error(f"Error deleting file '{fileInfo['file_name']}': {ex}")
                delete_results.append(False)
                # Continue with next file
        
        if not all(delete_results):
            logger.warning("Some files failed to delete, proceeding with workspace deletion")
        
        # Close and get a fresh connection for workspace deletion
        if db:
            try:
                db.conn.close()
            except:
                pass
        
        db = get_db()
        
        # Delete workspace record from DB
        try:
            ws_deleted = db.delete_workspace(workspace_id)
            if not ws_deleted:
                logger.error(f"Failed to delete workspace record for '{workspace_name}'")
                return False
        except Exception as e:
            logger.error(f"Error deleting workspace record: {e}")
            return False
            
        # Delete directories - doesn't need DB connections
        try:
            # Delete workspace directories
            workspace_upload_dir = os.path.join(cfg.UPLOAD_DIR, workspace_name)
            if os.path.exists(workspace_upload_dir):
                shutil.rmtree(workspace_upload_dir)
                logger.info(f"Deleted workspace directory: {workspace_upload_dir}")
            
            workspace_output_dir = os.path.join(cfg.OUTPUT_DIR, workspace_name)
            if os.path.exists(workspace_output_dir):
                shutil.rmtree(workspace_output_dir)
                logger.info(f"Deleted workspace output directory: {workspace_output_dir}")
        except Exception as e:
            logger.error(f"Error deleting workspace directories: {e}")
            # Continue anyway
                
        logger.info(f"Workspace '{workspace_name}' deleted successfully.")
        return True

    except Exception as e:
        logger.error(f"Error in delete_workspace_api: {e}")
        return False
    finally:
        # Always ensure connection is closed
        if db and hasattr(db, 'conn') and db.conn:
            try:
                db.conn.close()
                logger.debug("Database connection closed in finally block")
            except Exception as e:
                logger.error(f"Error closing DB connection: {e}")


def delete_file_api(workspaceInfo, fileInfo):
    """Delete a file and its associated records from the system"""
    db = get_db()  # Obtain a new Database instance from the pool
    try:
        workspace_name = workspaceInfo.get("workspace_name")
        file_name = fileInfo.get("file_name")
        workspace_id = workspaceInfo.get("id")
        file_id = fileInfo.get("id")
        
        if not workspace_name or not file_name:
            logger.error("Missing workspace_name or file_name in input parameters")
            return False
            
        logger.info(f"Deleting file '{file_name}' from workspace '{workspace_name}'")
        
        # First, handle doc_ids in workspace tables
        delete_success = True
        try:
            doc_ids = db.get_workspace_file_docIDs(workspace_id, file_id)
            if doc_ids:
                logger.info(f"Found {len(doc_ids)} doc_ids associated with file {file_id}")
                logger.info(f"Doc IDs: {doc_ids}")
                for doc_id_tuple in doc_ids:
                    logger.info(f"Processing doc_id: {doc_id_tuple}")
                    doc_id_value = doc_id_tuple['doc_id']
                    logger.info(f"Deleting doc_id {doc_id_value} from workspace_files_docid table")
                    deleted_docids = db.delete_workspace_file_docID(doc_id_value)
                    if deleted_docids:
                        logger.info(f"Deleted doc_id {doc_id_value} from workspace_files_docid table")
                    else:
                        logger.error(f"Failed to delete doc_id {doc_id_value} from workspace_files_docid table")
                # Now delete the file from the workspace_files table
                logger.info(f"Deleting file {file_id} from workspace_files table")
                deleted_file = db.delete_workspace_file(file_id)
                if deleted_file:
                    logger.info(f"Deleted file {file_id} from workspace_files table")
                else:
                    logger.error(f"Failed to delete file {file_id} from workspace_files table")
            else:
                logger.warning(f"No doc_ids found for file {file_id} in workspace {workspace_name}")
    
        except Exception as e:
            logger.error(f"Error handling workspace doc_ids: {str(e)}")
            # Continue with file deletion even if this fails
        
        # Determine if the file is a document or an image based on its extension
        file_extension = os.path.splitext(file_name)[1].lower()
        
        # Perform the specific deletion based on file type
        if file_extension in ALLOWED_IMAGE_EXTENSIONS:
            logger.info(f"Identified '{file_name}' as an image file")
            delete_success = delete_image(file_name, workspace_name)
        else:
            logger.info(f"Identified '{file_name}' as a document file")
            delete_success = delete_document(file_name, workspace_name)
            
        if delete_success:
            logger.info(f"Successfully deleted file '{file_name}' from workspace '{workspace_name}'")
        else:
            logger.error(f"Failed to delete file '{file_name}' from workspace '{workspace_name}'")
            
        return delete_success
        
    except Exception as e:
        logger.error(f"Error in delete_file_api: {e}")
        return False
    finally:
        # Always close the DB connection so it gets returned to the pool
        db.conn.close()


def delete_document(doc_name,workspace=None):
    db = get_db()
    try:
        
        doc_id = delete_from_docs_metadata(doc_name,workspace)
        
        if doc_id is None:
            logger.warning(f"Document {doc_name} not found in metadata.")
            return False

        vecor_store = VS.VectorStore()

        vecor_store.delete_from_text_collection(doc_id)

        #Delete from the all_files_list.json
        delete_file_from_list(doc_name,workspace)

        #Delete the document from output directory for docs only
        output_dir = cfg.OUTPUT_DIR
        if workspace:
            path = os.path.join(output_dir,workspace, doc_name)
        else:
            path=os.path.join(output_dir,doc_name)
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)  # remove read-only
            shutil.rmtree(path, ignore_errors=True)
            print("File deleted from output directory")
        else:
            print("file not found in output directory")
            

        #Delete the document from uploaded directory
        upload_dir = cfg.UPLOAD_DIR
        path=os.path.join(upload_dir,workspace,doc_name)
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)  # remove read-only
            os.remove(path)
        print("File also removed from upload directory")

        # Check if doc_id is a list or a single value
        if isinstance(doc_id, list):
            # It's a list - iterate through each doc_id
            for single_doc_id in doc_id:
                isDocID = db.get_contentPath_fromDocument(single_doc_id)
                if isDocID:
                    # Delete the document from the database
                    db.delete_doc(single_doc_id)
                    print(f"Deleted document with ID: {single_doc_id}")
                else:
                    print(f"Document with ID {single_doc_id} not found in database.")
        else:
            # It's a single value - process normally
            isDocID = db.get_contentPath_fromDocument(doc_id)
            if isDocID:
                # Delete the document from the database
                db.delete_doc(doc_id)
                print(f"Deleted document with ID: {doc_id}")
            else:
                print(f"Document with ID {doc_id} not found in database.")

        print(f"Document {doc_name} deleted successfully.")
        return True
    except Exception as e:
        print(f"Error deleting document: {e}")
        return  False
    finally:
        # Always close the DB connection so it gets returned to the pool
        db.conn.close()

def delete_image(image_name, workspace):
    try:
        # Find image in metadata to get doc_id
        doc_id = None
        doc_type = os.path.splitext(os.path.basename(image_name))[1].lower()
        
        with open(IMAGE_METADATA_PATH, "r") as file:
            data = json.load(file)
            
            # Iterate through all entries to find the matching image
            for key, value in data.items():
                # Check both workspace name and filename
                metadata_workspace = value.get('workspace_name', '')
                original_path = value.get('original_path', '')
                original_filename = os.path.basename(original_path)
                
                if metadata_workspace == workspace and original_filename == image_name:
                    doc_id = key  # The key in the JSON is the doc_id
                    break
        
        if doc_id is None:
            print(f"Image {image_name} not found in metadata for workspace {workspace}.")
            return False

        # Delete from vector store
        vecor_store = VS.VectorStore()
        vecor_store.delete_from_image_collection(doc_id)

        # Delete from the all_files_list.json
        delete_file_from_list(image_name, workspace)

        # Delete the image file from image storage directory
        image_dir = cfg.IMAGE_STORAGE_DIR
        path = os.path.join(image_dir, f"{doc_id}{doc_type}")
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)  # Remove read-only attribute
            try:
                os.remove(path)
                print(f"Image deleted from storage directory: {path}")
            except Exception as e:
                print(f"Failed to delete image file: {e}")
        else:
            print(f"Image file not found at {path}")

        # Delete from uploaded directory
        upload_dir = cfg.UPLOAD_DIR
        upload_path = os.path.join(upload_dir, workspace, image_name)
        if os.path.exists(upload_path):
            os.chmod(upload_path, stat.S_IWRITE)  # Remove read-only attribute
            try:
                os.remove(upload_path)
                print(f"Image deleted from upload directory: {upload_path}")
            except Exception as e:
                print(f"Failed to delete original uploaded file: {e}")
        
        # Delete the entry from metadata
        result = delete_from_image_metadata(doc_id, workspace)
        if result:
            print(f"Image metadata removed for doc_id: {doc_id}")

        print(f"Image {image_name} deleted successfully.")
        return True
    except Exception as e:
        print(f"Error deleting image: {e}")
        logger.error(f"Error deleting image {image_name} from workspace {workspace}: {str(e)}")
        return False

# here this function is delete the file details from the all_files_list.json
def delete_file_from_list(file_name: str,workspace,file_path=FILE_LIST):
    
    # Read the existing data from the JSON file
    try:
        with open(file_path, 'r+') as file:
            data = json.load(file)
            
            # Find the entry with the specified file name in the file_path
            updated_data = [entry for entry in data if file_name not in entry['file_path'] and entry['workspace_name']!=workspace]
            
            # Check if any entry was removed
            if len(data) != len(updated_data):
                # Write the updated data back to the JSON file
                file.seek(0)
                json.dump(updated_data, file, indent=2)
                file.truncate()
                logger.info(f"File name {file_name} deleted from the all file json list.")
            else:
                logger.warning(f"File name {file_name} not found in the list.")
    except Exception as e:
        print(f"Error deleting file name from list: {e}")

def delete_from_docs_metadata(doc_name: str,worskspace,file_path= DOCS_METADATA_PATH):
    """Delete a document entry from the JSON metadata file."""
    try:
        # Read the existing data from the JSON file
        with open(file_path, 'r+') as file:
            data = json.load(file)
            
            print("delete_from_docs_metadata :: doc_name =",doc_name)
            print("delete_from_docs_metadata :: worskspace =",worskspace)
            # Check if the doc_id exists in the data
            if doc_name in data and data[doc_name]['workspace_name'] == worskspace:
                # Remove the entry with the specified doc_id
                doc_id=data[doc_name]['doc_id']
                del data[doc_name]
                
                # Write the updated data back to the JSON file
                file.seek(0)
                json.dump(data, file, indent=2)
                file.truncate()
                print(f"Document {doc_name} deleted successfully from docs metadata.")
                return doc_id
            else:
                print(f"Document of id/name: {doc_name} not found in the metadata file {file_path}.")
                return None
    except Exception as e:
        print(f"Error deleting document: {e}")
        return None

def delete_from_image_metadata(doc_id: str,worskspace,file_path= IMAGE_METADATA_PATH):
    """Delete a document entry from the JSON metadata file."""
    try:
        # Read the existing data from the JSON file
        with open(file_path, 'r+') as file:
            data = json.load(file)
            
            # Check if the doc_id exists in the data
            if doc_id in data and data[doc_id]["workspace_name"]==worskspace:
                # Remove the entry with the specified doc_id
                del data[doc_id]
                
                # Write the updated data back to the JSON file
                file.seek(0)
                json.dump(data, file, indent=2)
                file.truncate()
                return doc_id
            else:
                print(f"Document of id/name: {doc_id} not found in the metadata file {file_path}.")
                return None
    except Exception as e:
        print(f"Error deleting document: {e}")
        return None



if __name__ == "__main__":
    doc_name="print.pdf"
    worskspce="workspace1w232"
    result=delete_document(doc_name,worskspce)
    print(result)

