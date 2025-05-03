import warnings
import pdfplumber
import camelot
import os
from pdf2image import convert_from_path
import pytesseract
import json
import json_functions as JC
from qa_chain import QAChain
from datetime import datetime
import config as cfg

#camelot.__ghostscript_path__ = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
#pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\rajsu\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'


OUTPUT_DIR = cfg.OUTPUT_DIR

class PDFExtractor:
    def __init__(self, pdf_path,workspace):
      #  pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\rajsu\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
        self.configure_paths()
        self.pdf_path = pdf_path
        output_dir = os.path.join(OUTPUT_DIR,workspace, os.path.basename(self.pdf_path))
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.images_dir = os.path.join(self.output_dir, "images")
        os.makedirs(self.images_dir, exist_ok=True)
    
    def configure_paths(self):
        # Check if running in Docker
        if os.path.exists('/.dockerenv'):
            # Docker paths
            camelot.__ghostscript_path__ = '/usr/bin/gs'
            pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
        else:
            # Windows paths
            camelot.__ghostscript_path__ = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
            pytesseract.pytesseract.tesseract_cmd = r'C:\\Users\\rajsu\\AppData\\Local\\Programs\\Tesseract-OCR\\tesseract.exe'
        

    def extract_text(self):
        text = {}
        with pdfplumber.open(self.pdf_path) as pdf:
            toal_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                print(f"Extracting text from page {i+1}/{toal_pages}...")
                # Try regular extraction first
                page_text = page.extract_text()
                if not page_text:
                    # Fallback to OCR using Tesseract
                    img = page.to_image(resolution=300)
                    page_text = pytesseract.image_to_string(img.original)
                text[f"page_{i+1}"] = page_text
        qa_chain = QAChain()
        content_to_ask = str(text) if len(
            str(text)) < 2000 else str(text)[:2000]
        self.doc_type = qa_chain.give_document_type(content_to_ask)
        print("Text is extracted from the pdf")
        return text

    def extract_tables(self):
        tables = {}
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                total_pages = len(pdf.pages)
            print(f"Extracting tables from {total_pages} pages...")

            for page_num in range(1, total_pages + 1):
                try:
                    # Extract tables for the current page with adjusted parameters
                    tables_list = camelot.read_pdf(
                        self.pdf_path,
                        flavor='stream',
                        pages=str(page_num),
                        edge_tol=500,  # Increase edge tolerance
                        row_tol=10     # Adjust row tolerance if needed
                    )
                    if tables_list:
                        for table in tables_list:
                            key = f"page_{page_num}"
                            # Append multiple tables from the same page
                            if key in tables:
                                tables[key] += "\n\n" + table.df.to_markdown()
                            else:
                                tables[key] = table.df.to_markdown()
                
                except Exception as e:
                    print(
                        f"Error extracting tables from page {page_num}: {str(e)}")
                    continue
            print("Tables are extracted from the pdf")
        except Exception as e:
            print(f"Error during table extraction: {str(e)}")
        return tables

    def extract_images(self):
        images = {}
        pages = convert_from_path(self.pdf_path, dpi=150)
        print(f"Extracting {len(pages)} images from PDF...")
        for i, page in enumerate(pages):
            print(f"Saving image {i+1}...")
            img_path = os.path.join(self.images_dir, f"page_{i+1}.jpg")
            page.save(img_path, "JPEG")
            images[f"page_{i+1}"] = img_path
        print("Images are extracted from the pdf")
        return images

    def extract_all(self,extract_tables=True):  
        data = {
            "text": self.extract_text(),
            "tables": self.extract_tables() if extract_tables else {},
            "images": self.extract_images(),
            "metadata": {
                "title": os.path.basename(self.pdf_path),
                "timestamp": datetime.utcnow().isoformat(),
                "source": self.pdf_path,
                "full_path": self.pdf_path,
                "document_type": self.doc_type
            }
        }
        print("pdf data is extracted")
        # Save to JSON
        json_path = os.path.join(self.output_dir, "extracted_data.json")
        with open(json_path, "w") as f:
            json.dump(data, f)
        print("json_path::", json_path)
        return json_path


if __name__ == "__main__":
    pdf_path = r"C:\Users\rajsu\Downloads\cp_plus_manual.pdf"
    extractor = PDFExtractor(pdf_path)
    json_path = extractor.extract_all(False)
    print(json_path)
