from sentence_transformers import SentenceTransformer  # Add this import
import torch
import clip
from PIL import Image
import numpy as np


class MultiModalEmbedder:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.text_model = SentenceTransformer('all-mpnet-base-v2')

        # CLIP remains for images
        self.clip_model, self.preprocess = clip.load(
            "ViT-B/32", device=self.device)

    def get_image_embedding(self, image_path):
        """Get 768-dim embedding for images using CLIP with padding"""
        image = Image.open(image_path).convert("RGB")
        image = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            embedding = self.clip_model.encode_image(image)

        embedding = embedding.cpu().numpy().flatten()
        if embedding.shape[0] < 768:
            padding = np.zeros(768 - embedding.shape[0])
            embedding = np.concatenate([embedding, padding])

        return embedding.tolist()

    def get_text_embedding(self, text):
        """Unified text embedding for all text content"""
        return self.text_model.encode(text).tolist()
