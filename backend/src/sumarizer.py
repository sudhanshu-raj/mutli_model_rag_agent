import json
import uuid
from dotenv import load_dotenv
import google.generativeai as genai
from sentence_transformers import SentenceTransformer
import os
from embedding_model import MultiModalEmbedder


load_dotenv()


class Summarizer:
    def __init__(self):
        self.embedder = MultiModalEmbedder()
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.gemini_model = genai.GenerativeModel("gemini-2.0-flash")

    def generate_summary(self, text, chunk_size=500000):
        chunks = [text[i:i+chunk_size]
                  for i in range(0, len(text), chunk_size)]
        summaries = []
        i=0
        for chunk in chunks:
            response = self.gemini_model.generate_content(
                f"Summarize this content briefly:\n{chunk}")
            print("this is round",i)
            i+=1
            
            summaries.append(response.text)
        return "\n".join(summaries)

    def generate_embeddings(self, text):
        """Use only local embeddings for all text types"""
        return self.embedder.get_text_embedding(text)


if __name__ == "__main__":
    summarizer = Summarizer()
    json_file = r"C:\Users\rajsu\Documents\multi_model_ragagent\media\output\cp_plus_manual.pdf\extracted_data.json"
    with open(json_file,"r") as f:
        data=json.load(f)
    metadata_lines = [
                    # Explicit source line
                    f"source: {data['metadata']['source']}",
                    f"title: {data['metadata']['title']}",
                    f"timestamp: {data['metadata']['timestamp']}",
                    f"document_type:{data['metadata']['document_type']}"

                ]

    full_text = " ".join(data["text"].values()) + \
        "\n\nMetadata:\n" + "\n".join(metadata_lines)
    summary = summarizer.generate_summary(full_text)
    print(summary) 