import os
import json
import re
import json_functions as JC
from qa_chain import QAChain
import time
import config as cfg
from pathlib import Path
from datetime import datetime

FILE_OUTPUT_DIR = cfg.OUTPUT_DIR

class TXT_Extractor:
    def __init__(self, file_path,workspace):
        self.file_path = file_path
         # Remove the extension and sanitize the filename
        self.filename = os.path.basename(file_path)
        self.output_dir = os.path.join(FILE_OUTPUT_DIR,workspace, self.filename)

        print("Creating output directory:", self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_all(self, raw=False):
        qa_chain = QAChain()
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if raw:
                return content  # Return raw text for chunking

            # Existing metadata structure
            content_to_ask = str(content) if len(
                str(content)) < 1000 else str(content)[:1000]
            self.doc_type = qa_chain.give_document_type(content_to_ask)
            data = {
                "text": {"content": content},
                "metadata": {
                    "source": self.file_path,
                    "title": os.path.basename(self.file_path),
                    "timestamp": datetime.utcnow().isoformat(),
                    "document_type": self.doc_type
                }
            }
            json_path = os.path.join(self.output_dir, "extracted_data.json")
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
            return data

        except UnicodeDecodeError:
            # Fallback encoding handling
            with open(self.file_path, 'r', encoding='latin-1') as f:
                content = f.read()

            content_to_ask = str(content) if len(
                str(content)) < 1000 else str(content)[:1000]
            self.doc_type = qa_chain.give_document_type(content_to_ask)

            data = {
                "text": {"content": content},
                "metadata": {
                    "source": self.file_path,
                    "title": os.path.basename(self.file_path),
                    "timestamp": datetime.utcnow().isoformat(),
                    "document_type": self.doc_type
                }
            }
            json_path = os.path.join(self.output_dir, "extracted_data.json")
            with open(json_path, "w") as f:
                json.dump(data, f, indent=4)
            return content if raw else data

    def extract_text(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        qa_chain = QAChain()
        content_to_ask = str(content) if len(
            str(content)) < 1000 else str(content)[:1000]
        self.doc_type = qa_chain.give_document_type(content_to_ask)
        return {"content": content}


if __name__=="__main__":
    extractor = TXT_Extractor(r"C:\Users\rajsu\Downloads\O2O_Platform.txt")
    full_content = extractor.extract_all()
    metadata=full_content["metadata"]
    print(metadata)

   