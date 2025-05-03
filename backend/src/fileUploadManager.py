import os
import requests
from urllib.parse import urlparse, unquote
import mimetypes
import time
from pathlib import Path
import shutil
import config as cfg
import sys
from logging_Setup import get_logger
from errorHandlers.fileManageErrorHandlers import FileSizeError, FileTypeError, DownloadError

logger=get_logger(__name__)


UPLOAD_DIR = cfg.UPLOAD_DIR
ALLWOED_EXTS = cfg.ALLWOED_EXTENSIONS


class FileManager:
    def __init__(self, download_dir=UPLOAD_DIR):
        """Initialize the FileManager with a download directory"""
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        
    def download_file(self, url, workspace_name=None, save_path=None, timeout=60, max_size_mb=15, check_exists=True):
        try:
            # Get filename and extension separately
            file_ext = self._get_extension_from_url(url)
            
            # Verify extension is allowed
            if file_ext.lower() not in ALLWOED_EXTS:
                raise FileTypeError(f"File extension {file_ext} not allowed. Allowed extensions: {', '.join(ALLWOED_EXTS)}")
            
            # Get filename from URL if not provided
            if not save_path:
                parsed_url = urlparse(url)
                filename = os.path.basename(unquote(parsed_url.path))
                
                # Handle URLs with no filename or no extension
                if not filename or os.path.splitext(filename)[1] == '':
                    # For URLs with no filename (like Unsplash)
                    if not filename:
                        filename = f"image_{int(time.time())}"
                    
                    # Make sure filename has the correct extension
                    if not filename.lower().endswith(file_ext):
                        filename = f"{os.path.splitext(filename)[0]}{file_ext}"
                        
                # Handle URLs with no clear filename
                if not filename or '?' in filename or filename.count('.') == 0:
                    # Generate a unique name with timestamp
                    name_components = []
                    
                    # Try to extract meaningful ID from path 
                    path_parts = [p for p in parsed_url.path.split('/') if p and p not in ('image', 'images', 'photo', 'photos')]
                    if path_parts:
                        # Use the last meaningful path component
                        name_components.append(path_parts[-1])
                    
                    # Add timestamp for uniqueness
                    name_components.append(str(int(time.time())))
                    
                    # Build filename
                    filename = "_".join(name_components)
                    
                    # Ensure it has the right extension
                    if not filename.endswith(file_ext):
                        filename = f"{filename}{file_ext}"

                if workspace_name:
                    save_path = os.path.join(self.download_dir,workspace_name, filename)
                else:
                    save_path = os.path.join(self.download_dir, filename)

            # Check if file already exists
            if check_exists and os.path.exists(save_path):
                logger.info(f"File already exists at {save_path}. Skipping download.")
                return {"path": save_path, "already_exists": True}
                
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Extract domain for referer
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Browser-like headers with dynamic referer
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": base_url
            }
            
            # First, make a HEAD request to check file size
            head_response = requests.head(url, timeout=timeout, headers=headers)
            content_length = int(head_response.headers.get('content-length', 0))
            
            # Convert MB to bytes (1 MB = 1,048,576 bytes)
            max_size_bytes = max_size_mb * 1048576
            
            # Check if file exceeds size limit
            if content_length > max_size_bytes and content_length > 0:
                raise FileSizeError(
                    f"File size ({self._humanize_size(content_length)}) exceeds limit of {max_size_mb}MB",
                    file_size=content_length,
                    size_limit=max_size_bytes
                )
                
            # Stream download to handle large files efficiently
            with requests.get(url, stream=True, timeout=timeout, headers=headers) as response:
                response.raise_for_status()  # Raise exception for 4XX/5XX responses
                
                # Get content length if available
                total_size = int(response.headers.get('content-length', 0))
                
                # Double-check size during actual download (in case HEAD was not accurate)
                if total_size > max_size_bytes and total_size > 0:
                    raise FileSizeError(f"File size ({self._humanize_size(total_size)}) exceeds limit of {max_size_mb}MB")
                    
                # Write the file
                with open(save_path, 'wb') as f:
                    if total_size == 0:  # If size unknown, monitor during download
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                downloaded += len(chunk)
                                # Check size during download if content-length wasn't provided
                                if downloaded > max_size_bytes:
                                    f.close()
                                    os.remove(save_path)
                                    raise FileSizeError(f"File size exceeds limit of {max_size_mb}MB during download")
                                f.write(chunk)
                    else:  # Stream in chunks
                        downloaded = 0
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                
                # After successful download, only process images - other file types don't need conversion
                if file_ext.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                    try:
                        # First, validate the image thoroughly
                        is_valid, error_message = self.validate_image(save_path)
                        
                        if not is_valid:
                            logger.error(f"Downloaded image is invalid: {error_message}")
                            os.remove(save_path)
                            raise DownloadError(f"Downloaded file is not a valid image: {error_message}")
                            
                        # Now proceed with processing for valid images
                        from PIL import Image
                        with Image.open(save_path) as img:
                            actual_format = img.format.lower() if img.format else None
                            
                            # If image is WebP, convert to PNG
                            if actual_format == 'webp':
                                logger.info(f"Converting WebP image to PNG: {save_path}")
                                png_path = os.path.splitext(save_path)[0] + '.png'
                                
                                # Convert with proper error handling
                                img = img.convert('RGBA')
                                img.save(png_path, 'PNG')
                                
                                # Remove original WebP file only if PNG saved successfully
                                if os.path.exists(png_path):
                                    if save_path != png_path and os.path.exists(save_path):
                                        os.remove(save_path)
                                    save_path = png_path
                                    logger.info(f"WebP image converted to PNG: {png_path}")
                            
                            # Handle wrong extensions
                            if actual_format:
                                correct_ext = f".{actual_format.lower()}"
                                current_ext = os.path.splitext(save_path)[1].lower()
                                
                                # Just log the mismatch but don't try to fix it
                                if current_ext != correct_ext and actual_format not in ('webp'):
                                    logger.info(f"File has incorrect extension: {current_ext} (actual format: {actual_format})")
                                    # Don't attempt to rename
                                    
                    except ImportError:
                        logger.warning("PIL not available for image processing")
                    except Exception as e:
                        logger.error(f"Error processing image: {str(e)}")
                        os.remove(save_path)
                        raise DownloadError(f"Error processing image: {str(e)}")
                
                # For PDFs, verify the file is valid (optional)
                elif file_ext.lower() == '.pdf':
                    try:
                        # Simple PDF header check
                        with open(save_path, 'rb') as f:
                            header = f.read(4)
                        if header != b'%PDF':
                            logger.warning(f"File doesn't have a valid PDF header: {save_path}")
                            # Note: We're not deleting or raising an error - some valid PDFs might not have standard headers
                    except Exception as e:
                        logger.warning(f"PDF validation warning: {str(e)}")
                
                # Return both the path and already_exists flag (False in this case)
                return {"path": save_path, "already_exists": False}
            
        except (FileTypeError, FileSizeError) as e:
            # Clean up partial download if exists
            if save_path and os.path.exists(save_path):
                os.remove(save_path)
            # Re-raise the specific exception
            raise
        except requests.exceptions.RequestException as e:
            # Clean up partial download
            if save_path and os.path.exists(save_path):
                os.remove(save_path)
            
            status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
            raise DownloadError(
                f"Error downloading file: {str(e)}", 
                url=url,
                status_code=status_code,
                original_error=e
            )
        except Exception as e:
            # Clean up partial download if exists
            if save_path and os.path.exists(save_path):
                os.remove(save_path)
            # Wrap other exceptions
            raise DownloadError(f"Error downloading file: {str(e)}") from e
    
    def get_file_details(self, file_path):
        """
        Get details about a file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            dict: Dictionary containing file details
            None: If file doesn't exist
        """
        if not os.path.exists(file_path):
            return None
            
        file_path = os.path.abspath(file_path)
        file_stat = os.stat(file_path)
        
        details = {
            "name": os.path.basename(file_path),
            "path": file_path,
            "size_bytes": file_stat.st_size,
            "size_human": self._humanize_size(file_stat.st_size),
            "modified_time": time.ctime(file_stat.st_mtime),
            "created_time": time.ctime(file_stat.st_ctime),
            "extension": os.path.splitext(file_path)[1].lower(),
            "mime_type": mimetypes.guess_type(file_path)[0] or "unknown",
            "is_directory": os.path.isdir(file_path)
        }
        
        return details
    
    def _get_extension_from_url(self, url):
        """Extract file extension from URL using multiple detection methods"""
        # Extract URL components
        parsed_url = urlparse(url)
        path = parsed_url.path
        query = parsed_url.query.lower()
        
        # 1. Check query parameters for format indicators
        format_indicators = {
            'fm=jpg': '.jpg',
            'fm=jpeg': '.jpg', 
            'fm=png': '.png',
            'format=jpg': '.jpg',
            'format=png': '.png',
            'format=pdf': '.pdf',
            'auto=webp': '.webp',
            'type=pdf': '.pdf',
            'type=document': '.docx'
        }
        
        for indicator, ext in format_indicators.items():
            if indicator in query:
                logger.info(f"Format detected from query parameters: {ext}")
                # Handle WebP conversion
                if ext == '.webp':
                    return '.png'
                return ext
        
        # 2. Check path extension
        ext = os.path.splitext(path)[1].lower()
        if ext:
            # Handle WebP conversion
            if ext == '.webp':
                return '.png'
            return ext
        
        # 3. Check Content-Type header
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            
            response = requests.head(url, timeout=10, headers=headers)
            content_type = response.headers.get('Content-Type', '').lower()
            base_content_type = content_type.split(';')[0].strip()
            
            # Map content types to extensions
            content_type_map = {
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/webp': '.png',  # Convert WebP to PNG
                'application/pdf': '.pdf',
                'application/msword': '.doc',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
                'text/plain': '.txt',
                'application/json': '.json',
                'text/markdown': '.md'
            }
            
            if base_content_type in content_type_map:
                return content_type_map[base_content_type]
        except Exception as e:
            logger.warning(f"Error determining content type: {str(e)}")
        
        # 4. Look for hints in the URL
        url_lower = url.lower()
        if 'pdf' in url_lower:
            return '.pdf'
        if 'doc' in url_lower and not 'docker' in url_lower:
            return '.docx'
        if '/image/' in path.lower() or 'photo' in path.lower():
            return '.jpg'
        
        # 5. Last resort - binary file
        return '.bin'
    
    def _humanize_size(self, size_bytes):
        """Convert bytes to human readable format"""
        if size_bytes == 0:
            return "0B"
            
        size_names = ("B", "KB", "MB", "GB", "TB", "PB")
        i = 0
        while size_bytes >= 1024 and i < len(size_names)-1:
            size_bytes /= 1024
            i += 1
        return f"{size_bytes:.2f} {size_names[i]}"
    
    def download_file_api(self, url, workspace_name, max_size_mb=15):
        """
        API friendly method to download a file from a URL
        
        Args:
            url (str): URL of the file to download
            workspace_name (str): Name of workspace to save file in
            max_size_mb (int): Maximum file size in MB
            
        Returns:
            dict: Dictionary with status, message and data (if successful)
        """
        try:
            result = self.download_file(url, workspace_name=workspace_name, max_size_mb=max_size_mb)
            file_details = self.get_file_details(result["path"])
            
            # Check if the file already existed
            if result["already_exists"]:
                logger.info(f"File already exists: {file_details['name']} | Size: {file_details['size_human']}")
                return {
                    "status": "success",
                    "message": "File already exists",
                    "data": file_details,
                    "already_exists": True
                }
            
            # Normal success case - file was downloaded
            logger.info(f"File downloaded successfully: {file_details['name']} | Size: {file_details['size_human']}")
            return {
                "status": "success",
                "message": "File downloaded successfully",
                "data": file_details,
                "already_exists": False
            }
        except FileTypeError as e:
            return {
                "status": "error",
                "error_type": "file_type_error",
                "message": e.message
            }
        except FileSizeError as e:
            return {
                "status": "error",
                "error_type": "file_size_error", 
                "message": e.message  # Use e.message instead of str(e)
            }
        except DownloadError as e:
            return {
                "status": "error",
                "error_type": "download_error",
                "message": e.message  # Use e.message instead of str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "error_type": "unknown_error",
                "message": f"An unexpected error occurred: {str(e)}"
            }

    def validate_image(self, image_path):
        """
        Thoroughly validates an image file to ensure it's not corrupted
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            bool: True if valid, False if invalid
            str: Error message if invalid, None if valid
        """
        if not os.path.exists(image_path):
            return False, "File does not exist"
            
        # Check file size - extremely small files are suspicious
        file_size = os.path.getsize(image_path)
        if file_size < 100:  # Less than 100 bytes is suspicious for an image
            return False, f"File too small ({file_size} bytes)"
        
        # Try multiple validation methods
        validation_errors = []
        
        # Method 1: Check file signature/magic numbers
        try:
            with open(image_path, 'rb') as f:
                header = f.read(12)  # Read first 12 bytes
                
            # Check for common image signatures
            is_jpeg = header.startswith(b'\xff\xd8\xff')
            is_png = header.startswith(b'\x89PNG\r\n\x1a\n')
            is_gif = header.startswith(b'GIF87a') or header.startswith(b'GIF89a')
            is_webp = header.startswith(b'RIFF') and b'WEBP' in header
            
            if not any([is_jpeg, is_png, is_gif, is_webp]):
                validation_errors.append("Invalid image signature")
        except Exception as e:
            validation_errors.append(f"Signature check error: {str(e)}")
        
        # Method 2: Try to open with PIL and verify
        try:
            from PIL import Image, UnidentifiedImageError
            try:
                with Image.open(image_path) as img:
                    # Verify the file
                    img.verify()
                    
                    # If we get here, basic verification passed
                    # For extra validation, try to access image properties
                    _ = img.mode  # This will fail for some corrupt images
                
                # Try loading again (verify closes the file)
                with Image.open(image_path) as img:
                    # Try to load the image data - this catches more issues
                    img.load()
                    
                    # Check for reasonable dimensions (not absurdly large)
                    width, height = img.size
                    if width <= 0 or height <= 0 or width > 20000 or height > 20000:
                        validation_errors.append(f"Suspicious dimensions: {width}x{height}")
            except UnidentifiedImageError:
                validation_errors.append("PIL cannot identify image format")
            except Exception as e:
                validation_errors.append(f"PIL validation error: {str(e)}")
        except ImportError:
            validation_errors.append("PIL not available for validation")
        
        # If we have errors from both methods, the image is likely invalid
        if validation_errors:
            # Log the specific errors
            error_message = "; ".join(validation_errors)
            logger.warning(f"Image validation failed: {image_path} - {error_message}")
            return False, error_message
            
        # If we got here, all checks passed
        return True, None


# Example usage
if __name__ == "__main__":
    file_manager = FileManager()
    
    # Download a file
    pdf_url = "https://i.pinimg.com/originals/0a/b8/ce/0ab8ce6d94dc4bd5183e953ad6ef797d.gif"
    # downloaded_path = file_manager.download_file(pdf_url)
    
    # if downloaded_path:
    #     # Get and display file details
    #     details = file_manager.get_file_details(downloaded_path)
    #     print("\nFile Details:")
    #     for key, value in details.items():
    #         print(f"{key}: {value}")
    # else: 
    result=file_manager.download_file_api(pdf_url)
    if result:
        print(result)