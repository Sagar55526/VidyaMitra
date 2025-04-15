from sentence_transformers import SentenceTransformer, util

# ✅ Load SBERT model only once (Efficiency)
sbert_model = SentenceTransformer("all-MiniLM-L6-v2")

def calculate_similarity(text1, text2):
    """Calculate semantic similarity using SBERT."""

    if not text1 or not text2:
        return 0.0  # Return lowest similarity for empty inputs

    try:
        # Encode sentences using SBERT
        embeddings = sbert_model.encode([text1, text2], convert_to_tensor=True)
        
        # Compute cosine similarity
        similarity_score = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
        
        return round(similarity_score, 2)

    except Exception as e:
        print(f"Error calculating similarity: {e}")
        return 0.0  # Return lowest similarity in case of error

