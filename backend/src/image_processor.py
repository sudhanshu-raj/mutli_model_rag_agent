import os
import cv2
import pytesseract
from PIL import Image
import json
from vector_store import VectorStore  # Updated import path
import uuid
import numpy as np
from embedding_model import MultiModalEmbedder  # Updated import path
from datetime import datetime
import config as cfg
from logging_Setup import get_logger

logger = get_logger(__name__)

IMAGES_METDATA_FILE =cfg.IMAGES_METADATA_FILE
IMAGE_STORAGE_DIR = cfg.IMAGE_STORAGE_DIR

class ImageProcessor:
    def __init__(self, storage_dir=IMAGE_STORAGE_DIR, metadata_file=IMAGES_METDATA_FILE):
        self.storage_dir = storage_dir
        self.metadata_file = metadata_file
        os.makedirs(self.storage_dir, exist_ok=True)
        self.embedder = MultiModalEmbedder()

    def process_image(self, image_path, user_metadata):
        """Process an image file and store its data"""
        try:
            # Generate unique ID
            doc_id = str(uuid.uuid4())

            user_description={
                "title":user_metadata.get("image_name", "Untitled Image"),
                "description":user_metadata.get("image_description", "")
            }

            # Extract text from image
            extracted_text = self._extract_text_from_image(image_path)
            extracted_text = f"Image_title: {user_description['title']}\nImage_description_ByUser: {user_description['description']}\n\n Content: {extracted_text}"

            # Generate embeddings
            text_embedding = self.embedder.get_text_embedding(extracted_text)
            image_embedding = self.embedder.get_image_embedding(image_path)

            # Combine embeddings with weighted average
            combined_embedding = (
                np.array(text_embedding) * 0.6 +
                np.array(image_embedding) * 0.4
            ).tolist()

            # Create metadata
            metadata = {
                "title": user_metadata.get("title", "Untitled Image"),
                "timestamp": datetime.utcnow().isoformat(),
                "document_type": "image",
                "user_description": user_metadata.get("description", ""),
                "original_path": image_path,
                "extracted_text": extracted_text,
                "workspace_name":user_metadata.get("workspace_name","")
            }

            # Store in vector database
            vs = VectorStore()
            vs.add_image_embedding(
                doc_id=doc_id,
                embedding=combined_embedding,
                text=extracted_text,
                metadata=metadata
            )

            # Update JSON metadata anf store image copy
           # self._store_image_copy(image_path, doc_id)
            self._update_metadata_file(doc_id, metadata)
            logger.info(f"Image processed successfully: {doc_id}")
            return doc_id

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return None

    def _extract_text_from_image(self, image_path):
        """Use OCR to extract text from image"""
        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            processed = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            text = pytesseract.image_to_string(processed)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {str(e)}")
            return ""

    def _store_image_copy(self, original_path, doc_id):
        """Store image in organized directory structure"""
        ext = os.path.splitext(original_path)[1]
        new_filename = f"{doc_id}{ext}"
        new_path = os.path.join(self.storage_dir, new_filename)

        with Image.open(original_path) as img:
            img.save(new_path)
        return new_path

    def _update_metadata_file(self, doc_id, metadata):
        """Update the central metadata JSON file"""
        try:
            # Initialize empty data if file doesn't exist
            if not os.path.exists(self.metadata_file):
                data = {}
            else:
                # Handle empty file case
                if os.path.getsize(self.metadata_file) == 0:
                    data = {}
                else:
                    with open(self.metadata_file, "r") as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError:
                            print("Corrupted metadata file, resetting...")
                            data = {}

            data[doc_id] = metadata

            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Metadata update failed: {str(e)}")
            # Create empty file as fallback
            with open(self.metadata_file, "w") as f:
                json.dump({}, f)
