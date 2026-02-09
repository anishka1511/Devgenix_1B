from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load local model (path can be changed)
model = SentenceTransformer("BAAI/bge-small-en-v1.5")

def get_embedding(text):
    return model.encode(text, convert_to_numpy=True)

def get_similarity_score(query_embedding, section_embedding):
    return float(cosine_similarity([query_embedding], [section_embedding])[0][0])
