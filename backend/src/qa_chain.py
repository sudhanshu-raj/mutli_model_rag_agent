import io
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAI
from tenacity import retry, wait_exponential_jitter, stop_after_attempt
import time
from PIL import Image
import os
from dotenv import load_dotenv
load_dotenv()
import config as cfg
media_output_dir=cfg.OUTPUT_DIR
base_url=cfg.BASE_URL
upoad_dir=cfg.UPLOAD_DIR

class QAChain:
    def __init__(self):
        self.llm = GoogleGenerativeAI(
            model="gemini-2.0-flash",  
            temperature=0,
            max_retries=5,  # Explicit retries
            request_timeout=30, # Timeout in seconds
            api_key=os.environ.get("GEMINI_API_KEY")
        )
        self.model = self.llm
        self.last_call_time = 0

    @retry(wait=wait_exponential_jitter(initial=2, max=60),
           stop=stop_after_attempt(5),
           reraise=True)
    def _safe_llm_call(self, messages):
        # Enforce rate limiting
        elapsed = time.time() - self.last_call_time
        if elapsed < 1.2:  # 50 RPM limit (1.2s between calls)
            time.sleep(1.2 - elapsed)

        return self.llm.invoke(messages)

    def generate_answer(self, context_list, question):
        # Extract image paths from context
        image_paths = []
        context_text = ""
        context_table = ""
        for context in context_list:
            for page in context.get("images", {}).values():
                images = page if isinstance(page, list) else [page]
                for img in images:
                    relative_path = os.path.relpath(os.path.abspath(img), start=media_output_dir).replace("\\", "/")
                    # now add the file url
                    file_url=f"{base_url}fileAccess/outputfiles/{relative_path}"
                    image_paths.append(file_url)

            text = context.get("text", "")
            if isinstance(text, dict):
                text = "\n".join(f"{key}: {value}" for key,
                                 value in text.items())

            context_text += text

            # Safe table handling for all document types
            # Use empty dict if no tables exist
            table = context.get('tables', {})

            # Rest of your existing table processing code
            if table:
                table_str = "\n".join(
                    [f"Table {idx}:\n{tbl}" for idx, tbl in enumerate(table.values())])
            else:
                table_str = "No relevant tables found"
            context_table += table_str
       
        print("image_paths::", image_paths)
        prompt = f"""
        Context: {context_text}
        Tables: {context_table}
        Images: Available at paths - {image_paths}

        Question: {question}
        Answer with text and REFER TO IMAGES LIKE THIS in the end of answer : [Image: Given Image path].
        DO NOT INVENT IMAGES THAT DON'T EXIST.And don't repeat your same answer.
        Can you please respond in a friendly and helpful tone?
        I'd really appreciate it if your answers were well-formatted using clean and readable Markdown,
        with Proper spacing and structure,Nice formatting like bold, italics, bullet points, etc. 
        and Meaningful and fun emojis where they make sense.
        """
        try:
            # return self.llm.invoke(prompt)
            answer = self._safe_llm_call([prompt])
            seen = set()
            deduped_lines = []
            for line in answer.split('\n'):
                clean_line = line.strip().lower()
                if clean_line and clean_line not in seen:
                    seen.add(clean_line)
                    deduped_lines.append(line)

            return "\n".join(deduped_lines)
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            return "I'm having trouble accessing the AI service. Please try again later."

    def generate_answer_image(self, context_list, question):
        # Extract image paths and text context
        image_paths = []
        text_context = []

        for context in context_list:
            # print("current context is  :::")
            # print(context)
            # # Get image path from metadata
            # img_path = context.get('metadata', {}).get('original_path') or \
            #     context.get('metadata', {}).get('source', '')
            # if img_path:
            #     image_paths.append(img_path)

            # Build text context from available fields
            entry = []
            if context.get('text', {}).get('content'):
                entry.append(f"Extracted text: {context['text']['content']}")
            if context['metadata'].get('extracted_text'):
                entry.append(
                    f"OCR text: {context['metadata']['extracted_text']}")
            if context['metadata'].get('user_description'):
                entry.append(
                    f"User description: {context['metadata']['user_description']}")
            if context['metadata'].get('title'):
                entry.append(f"Title: {context['metadata']['title']}")
            if context.get('metadata').get('original_path'):
                image_original_path= context['metadata'].get('original_path')
                relative_path = os.path.relpath(os.path.abspath(image_original_path), start=upoad_dir).replace("\\", "/")
                # now add the file url
                file_url=f"{base_url}fileAccess/files/{relative_path}"
                image_paths.append(file_url)
                entry.append(
                    f"Source :{file_url}")
            # if context.get('metadata').get('source'):
            #     entry.append(f"Source: {context['metadata']['source']}")

            text_context.append("\n".join(entry))

        # Build prompt
        prompt = f"""
        Analyze the image description if given and the metadata like title, User description,source, image paths etc:
        {text_context}

        Question: {question}

        Asnwer with short description and reference to image path like this :[Image: Path of source].
        And Do not repeat your same answer.
        """

        try:
            # Pass formatted message to Gemini
            answer = self._safe_llm_call([prompt])

            seen = set()
            deduped_lines = []
            for line in answer.split('\n'):
                clean_line = line.strip().lower()
                if clean_line and clean_line not in seen:
                    seen.add(clean_line)
                    deduped_lines.append(line)

            return "\n".join(deduped_lines)

        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return "I'm having trouble accessing the AI service. Please try again later."

    # it is same like generate_answer_image but it add the images to process
    def generate_answer_image_V2(self, context_list, question):
        # Extract image paths and text context
        image_paths = []
        text_context = []

        for context in context_list:
            print("current context is  :::")
            print(context)
            # Get image path from metadata
            img_path = context.get('metadata', {}).get('original_path') or \
                context.get('metadata', {}).get('source', '')
            if img_path:
                image_paths.append(img_path)

            # Build text context from available fields
            entry = []
            if context.get('text', {}).get('content'):
                entry.append(f"Extracted text: {context['text']['content']}")
            if context['metadata'].get('extracted_text'):
                entry.append(
                    f"OCR text: {context['metadata']['extracted_text']}")
            if context['metadata'].get('user_description'):
                entry.append(
                    f"User description: {context['metadata']['user_description']}")
            if context['metadata'].get('title'):
                entry.append(f"Title: {context['metadata']['title']}")

            text_context.append("\n".join(entry))

        # Convert images to Gemini-compatible format
        image_parts = []
        valid_image_paths = []
        for path in image_paths:
            try:
                img = Image.open(path)
                img_byte_arr = io.BytesIO()
                img.convert("RGB").save(img_byte_arr, format='JPEG')
                image_parts.append({
                    "mime_type": "image/jpeg",
                    "data": img_byte_arr.getvalue()
                })
                valid_image_paths.append(path)
            except Exception as e:
                print(f"Error processing image {path}: {str(e)}")

        # Build prompt
        prompt = f"""
        Analyze these images and related context:
        {text_context}
        
        Question: {question}
        
        Requirements:
        1. Reference images by their filename like [Image:filename.jpg]
        2. Use ONLY the provided images and context
        3. For visual questions, describe key elements from images
        4. Keep technical analysis under 3 sentences
        """

        # Build proper message format
        message = {
            "role": "user",
            "content": [
                {"text": prompt},
                *[
                    {
                        "inline_data": {
                            "mime_type": part["mime_type"],
                            "data": part["data"]
                        }
                    } for part in image_parts
                ]
            ]
        }

        try:
            # Pass formatted message to Gemini
            answer = self._safe_llm_call([message])

            # Post-processing
            final_image_refs = [
                f"[Image:{os.path.basename(p)}]" for p in valid_image_paths]
            return {
                "answer": answer.strip(),
                "image_references": final_image_refs,
                "source_paths": valid_image_paths
            }

        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return {
                "answer": "Unable to analyze images at this time",
                "image_references": [],
                "source_paths": []
            }

    def validate_context_relevance(self, context, question):


        prompt = f"""
        Determine if this context is relevant to the question. 
        Answer ONLY 1 for relevant or 0 for irrelevant.
        
        Question: {question}
        Context: {str(context)[:2000]}
        """
        try:
            response = self.llm.invoke(prompt)
            return float(response.strip()) if response.strip().isdigit() else 0.0
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            return 0.0  # Fallback to assuming irrelevant

    def give_document_type(self, context):
        prompt = f"""
            You are given the text content of a document. Analyze it and determine its type based on its content.  
            Possible categories include:  

            #### **Personal & Business Documents**  
            - **WiFi Bill** (mentions internet service providers, billing cycles, or data usage)  
            - **Phone Bill** (contains mobile carrier details, call records, or monthly charges)  
            - **Invoice** (mentions payment details, transaction history, or billing items)  
            - **Bank Statement** (includes transactions, account balances, financial data)  
            - **Tax Document** (mentions income tax, deductions, or government tax forms)  
            - **Insurance Document** (mentions policy details, claims, premium amounts)  
            - **Learning Notes** (lot of topics,structured data, lots of concepts)
            - **Certificate/Academic Transcript** (mentions grades, courses, academic achievements)

            #### **Professional & Corporate Documents**  
            - **Resume/CV** (has sections like 'Work Experience', 'Skills', 'Education', etc.)  
            - **Business Report** (contains executive summaries, financial analysis, recommendations)  
            - **Project Documentation** (technical specs, APIs, or development workflows)  
            - **Legal Document** (contracts, terms & conditions, agreements, NDAs)  

            #### **Technical & Research Documents**  
            - **Academic Paper/Research Paper** (contains citations, references, structured research)  
            - **Assignment/Homework** (structured academic content, problem statements, or solutions)  
            - **Technical Report** (engineering/IT reports, system documentation, whitepapers)  
            - **Medical Report** (health data, test results, doctor notes, prescriptions)  
            - **Product Documentation** (product detailed information, product data)

            #### **Security & Confidential Documents**  
            - **Credentials File** (includes usernames, passwords, API keys, or login information)  
            - **Confidential Report** (mentions classified information, security logs, sensitive business data)  
            - **Audit Report** (includes financial or security compliance checks)  

            #### **Others**  
            - **Government Forms** (passport applications, voting documents, official forms)  
            - **E-books/Manuals** (long structured text with chapters and guides)  
            - **Meeting Minutes** (notes from discussions, agendas, decisions made)  
            - **General Notes** (random notes, unstructured data, rough drafts)  
            - **Other** (if none of the above categories apply)  

            ---

            ### **Context:**  
            {context}  

            ### **Instruction:**  
            Analyze the content and respond with the most appropriate category from the list above.  
            If the document appears to fit multiple categories, return the **most relevant one**.  
            If uncertain, choose `"Other"` and provide a short explanation.
            """
        try:
            # return self.llm.invoke(prompt)
            return self._safe_llm_call([prompt]).replace("\n", "")
        except Exception as e:
            print(f"LLM Error: {str(e)}")

    def expand_query(self, original_query):
        try:
            expanded = self._safe_llm_call(
                [f"Expand this search query with synonyms and related terms: {original_query}"]
            )
            return f"{original_query} {expanded}"
        except Exception as e:
            print(f"Query expansion failed: {e}")
            return original_query



