from datetime import datetime
from pdf_extractor import PDFExtractor
from sumarizer import Summarizer
from database import Database
from vector_store import VectorStore
import uuid
import json
import os
from word_doc_extractor import WordExtractor
from text_extractor import TXT_Extractor
import json_functions as JC
from image_processor import ImageProcessor
from helper_functions import is_file_too_large,revert_fileAdded
import util
from logging_Setup import get_logger
import config as cfg    
from errorHandlers.fileManageErrorHandlers import FileSizeError, FileTypeError, FileAlreadyExistsError
from gemini_direct import generate_image_title_dscrpt

logger=get_logger(__name__)

def process_files(file_path, image_metadata=None, workspace_name=None, error_context=None):
    try:
        # Run pre-process checks first
        pre_process_check(file_path, workspace_name)
        
        logger.info("Processing the File...")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()

        if ext.lower() in [".png", ".jpg", ".jpeg"]:
            logger.info("Processing the image...")
            processor = ImageProcessor()
            image_metadata["workspace_name"]=workspace_name
            return processor.process_image(file_path, image_metadata or {})
        elif ext in [".txt", ".md"]:
            logger.info(f"Processing large TXT file: {file_path}")
            extractor = TXT_Extractor(file_path,workspace_name)

            # Get raw text and metadata directly from extractor
            logger.info("Getting raw content and metadata")
            extracted_content = extractor.extract_all()

            full_content = extracted_content["text"]["content"]
            metadata=extracted_content["metadata"]
            metadata["workspace_name"]=workspace_name

            # Split into chunks
            logger.debug("Splitting text into chunks")
            logger.info(f"Splitting {len(full_content)} characters into chunks")
            chunk_size = 4000
            chunks = [full_content[i:i+chunk_size]
                      for i in range(0, len(full_content), chunk_size)]

            vs = VectorStore()
            doc_id = str(uuid.uuid4())

            # Process each chunk with shared metadata
            logger.info("Processing each chunk with shared metadata")
            doc_id_list=[]
            for idx, chunk in enumerate(chunks):
                chunk_metadata = {
                    "source": metadata["source"],
                    "title": metadata["title"],
                    "timestamp": metadata["timestamp"],
                    "document_type": metadata["document_type"],
                    "chunk": idx+1,
                    "total_chunks": len(chunks),
                    "workspace_name":metadata["workspace_name"]
                }

                # Generate embeddings for each chunk
                logger.debug(f"Generating embeddings for chunk {idx+1}/{len(chunks)}")
                embedding = Summarizer().generate_embeddings(chunk)
                vs.add_embedding(
                    doc_id=f"{doc_id}-{idx}",
                    embedding=embedding,
                    text=chunk,
                    metadata=chunk_metadata
                )
                doc_id_list.append(f"{doc_id}-{idx}")

            logger.info(f"Processed TXT file into {len(chunks)} chunks")
            #Saving the text metadata in docs_metadata.json
            file_name = os.path.basename(file_path)
            metadata["output_path"]=f"media/output/{file_name}"
            metadata["doc_id"]=doc_id_list
            JC._update_DOCX_metadata_file(file_name, metadata)
            return doc_id_list
        # reached here means it is a PDF or DOCX file
        else:
            isLargeFile=is_file_too_large(file_path,5)
            if ext == '.pdf':
                extractor = PDFExtractor(file_path,workspace_name)
            elif ext == '.docx':
                extractor = WordExtractor(file_path,workspace_name)
            else:
                raise ValueError(f"Unsupported file type: {ext}")

            json_path = extractor.extract_all(extract_tables=False)  #extract_tables=False if isLargeFile else True

            # Generate Summary & Embeddings
            with open(json_path, "r") as f:
                data = json.load(f)
            metadata_lines = [
                # Explicit source line
                f"source: {data['metadata']['source']}",
                f"title: {data['metadata']['title']}",
                f"timestamp: {data['metadata']['timestamp']}",
                f"document_type:{data['metadata']['document_type']}",
                f"workspace_name:{workspace_name}"
            ]
            
            full_text = " ".join(data["text"].values()) + \
                "\n\nMetadata:\n" + "\n".join(metadata_lines)

            logger.debug("Generating summary and embeddings")
            summarizer = Summarizer()
            summary = summarizer.generate_summary(full_text)
            embedding = summarizer.generate_embeddings(summary)

            # Store Data
            doc_id = str(uuid.uuid4())
            db = Database()
            db.insert_document(doc_id, data["metadata"]["title"], workspace_name,
                               data["metadata"]["timestamp"], json_path)

            vs = VectorStore()
            metadata_dict = {
                "source": f"{data['metadata']['source']}",
                "title": f"{data['metadata']['title']}",
                "timestamp": f"{data['metadata']['timestamp']}",
                "document_type": f"{data['metadata']['document_type']}",
                "workspace_name": workspace_name
            }
            vs.add_embedding(
                doc_id=doc_id,
                embedding=embedding,
                text=summary,
                metadata=metadata_dict
            )
            logger.info(f"Processed {ext} file into {doc_id}")
            file_name = os.path.basename(file_path)
            metadata_dict["output_path"]=f"media/output/{file_name}"
            metadata_dict["doc_id"]=doc_id
            #Saving the text metadata in docs_metadata.json
            JC._update_DOCX_metadata_file(file_name, metadata_dict)
            return doc_id
    
    except (FileSizeError, FileTypeError) as e:
        logger.error(f"Cannot process file: {str(e)}")
        
        # Store error details if context object provided
        if error_context is not None:
            error_context["error_occurred"] = True
            error_context["error_details"] = {
                "exception": e,
                "location": "pre_process_check"
            }
        revert_fileAdded(file_path)
        return None
    except FileAlreadyExistsError as e:
        logger.warning(f"Cannot process file: {str(e)}")
        
        # Store error details if context object provided
        if error_context is not None:
            error_context["error_occurred"] = True
            error_context["error_details"] = {
                "exception": e,
                "location": "pre_process_check"
            }
        return None
    except Exception as e:
        logger.error(f"Error occurred while adding file: {e}")
        
        # Store error details if context object provided
        if error_context is not None:
            error_context["error_occurred"] = True
            error_context["error_details"] = {
                "exception": e,
                "location": "process_files"
            }
            
        # Cleanup code...
        revert_fileAdded(file_path) 
        return None


def pre_process_check(file_path, workspace_name=None):
    """
    Check if the file is too large(>10mb), supports allowed extensions only and not already exists before process.
    Raises appropriate exceptions instead of returning False.
    """
    try:
        
        # Check if file already exists
        if not JC.add_file_to_json(file_path, os.path.splitext(file_path)[1].lower(), workspace_name):
            file_name = os.path.basename(file_path)
            raise FileAlreadyExistsError(
                f"File '{file_name}' already exists in the workspace",
                file_path=file_path,
                file_name=file_name
            )
            
        # Check file size
        if is_file_too_large(file_path):
            file_size = os.path.getsize(file_path)
            raise FileSizeError(
                f"File size ({file_size} bytes) exceeds the maximum limit of 10MB",
                file_size=file_size,
                size_limit=cfg.MAX_FILE_SIZE_MB,
            )
            
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in cfg.ALLWOED_EXTENSIONS:
            raise FileTypeError(
                f"File type '{ext}' is not supported. Allowed types: {', '.join(cfg.ALLWOED_EXTENSIONS)}",
                file_ext=ext,
                allowed_exts=cfg.ALLWOED_EXTENSIONS
            )
        
        return True
        
    except (FileAlreadyExistsError, FileSizeError, FileTypeError) as e:
        # Log the specific error
        #logger.warning(f"Pre-process check failed: {str(e)}")
        # Re-raise to be caught by the caller
        raise
    except Exception as e:
        logger.error(f"Unexpected error in pre-process check: {str(e)}")
        raise Exception(f"Error checking file: {str(e)}")

def process_files_api(file_path, image_metadata=None, workspace_name=None):
    """API-friendly method to process files of various types."""
    try:
        # Check if file_path is None or empty
        if not file_path:
            return {
                "status": "error",
                "message": "No file path provided",
                "error_type": "missing_parameter"
            }

        # Construct full path with upload directory and workspace
        try:
            print(f"file_path is {file_path}")
            print(f"workspace_name is {workspace_name}")
            print(f"image_metadata is {image_metadata}")

            upload_dir = cfg.UPLOAD_DIR
            if workspace_name:
                full_path = os.path.join(upload_dir, workspace_name, file_path)
            else:
                full_path = os.path.join(upload_dir, file_path)
        except Exception as path_error:
            return {
                "status": "error",
                "message": f"Error constructing file path: {str(path_error)}",
                "error_type": "path_error"
            }
        
        # Create error tracking context
        error_context = {"error_occurred": False, "error_details": None}
        
        # Pass error context to process_files
        doc_id = process_files(full_path, image_metadata, workspace_name, error_context)
        
        if doc_id:
            # Success case - file was processed
            file_name = os.path.basename(full_path)
            file_ext = os.path.splitext(full_path)[1].lower()
            
            return {
                "status": "success",
                "message": f"File processed successfully",
                "data": {
                    "doc_id": doc_id,
                    "file_name": file_name,
                    "file_type": file_ext,
                    "workspace": workspace_name,
                    "timestamp": datetime.now().isoformat()
                }
            }
        else:
            # Handle case where process_files returned None but captured error details
            if error_context["error_occurred"]:
                error_details = error_context["error_details"]
                
                if isinstance(error_details["exception"], FileAlreadyExistsError):
                    return {
                        "status": "error",
                        "message": str(error_details["exception"]),
                        "error_type": "file_already_exists",
                        "details": {
                            "file_name": os.path.basename(full_path)
                        }
                    }
                elif isinstance(error_details["exception"], FileSizeError):
                    e = error_details["exception"]
                    return {
                        "status": "error",
                        "message": str(e),
                        "error_type": "file_too_large",
                        "details": {
                            "file_size": e.details.get("file_size"),
                            "size_limit": e.details.get("size_limit"),
                            "file_name": os.path.basename(full_path)
                        }
                    }
                elif isinstance(error_details["exception"], FileTypeError):
                    e = error_details["exception"]
                    return {
                        "status": "error",
                        "message": str(e),
                        "error_type": "invalid_file_type",
                        "details": {
                            "file_type": e.details.get("file_ext"),
                            "allowed_types": e.details.get("allowed_exts"),
                            "file_name": os.path.basename(full_path)
                        }
                    }
                else:
                    # Some other captured exception
                    return {
                        "status": "error",
                        "message": str(error_details["exception"]),
                        "error_type": "processing_error",
                        "details": {
                            "file_name": os.path.basename(full_path),
                            "error_location": error_details.get("location", "unknown")
                        }
                    }
            
            # Fall back to generic error if no details available
            return {
                "status": "error",
                "message": "File processing failed for unknown reasons",
                "error_type": "processing_failed"
            }
    
    # Add the missing exception handlers
    except FileNotFoundError as e:
        logger.error(f"API request - file not found: {file_path}")
        return {
            "status": "error",
            "message": str(e),
            "error_type": "file_not_found",
            "details": {
                "file_path": file_path
            }
        }
        
    except (FileAlreadyExistsError, FileSizeError, FileTypeError) as e:
        # These should be caught above in process_files, but handle them here too
        logger.error(f"API request - file validation error: {str(e)}")
        
        error_type = "validation_error"
        if isinstance(e, FileAlreadyExistsError):
            error_type = "file_already_exists"
        elif isinstance(e, FileSizeError):
            error_type = "file_too_large"
        elif isinstance(e, FileTypeError):
            error_type = "invalid_file_type"
            
        return {
            "status": "error",
            "message": str(e),
            "error_type": error_type
        }
        
    except Exception as e:
        # Log the unexpected error
        logger.error(f"Unexpected error in process_files_api: {str(e)}")
        
        # Generic error response
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}",
            "error_type": "unexpected_error"
        }
    
def generate_image_description(image_path):
    """
    Generate a title and description for an image using the ImageProcessor class.
    """
    try:
        upload_dir = cfg.UPLOAD_DIR
        full_path = os.path.join(upload_dir, image_path)
        if os.path.exists(full_path) == False:
            raise FileNotFoundError(f"File not found: {full_path}")
        title_descrption = generate_image_title_dscrpt(full_path)
        return title_descrption.get("description","")
    except Exception as e:
        logger.error(f"Error generating image title & description: {str(e)}")
        return None