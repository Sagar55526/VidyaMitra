from sentence_transformers import SentenceTransformer, util
import torch

asag_model = SentenceTransformer("all-mpnet-base-v2")

def grade_answer(user_answer, model_answer):
    """
    Grades the user's answer based on semantic similarity to the model answer.
    Returns a score out of 5 with a brief explanation.
    """
    user_embedding = asag_model.encode(user_answer, convert_to_tensor=True)
    model_embedding = asag_model.encode(model_answer, convert_to_tensor=True)
    
    similarity = util.pytorch_cos_sim(user_embedding, model_embedding).item()
    
    if similarity >= 0.90:
        grade = 5 
    elif similarity >= 0.80:
        grade = 4 
    elif similarity >= 0.70:
        grade = 3 
    elif similarity >= 0.60:
        grade = 2 
    elif similarity >= 0.50:
        grade = 1
    else:
        grade = 0
        
    
    return grade

    # 535fdd81bff84f2b857754f057d4f4d5
    # https://polygon-mainnet.infura.io/v3/535fdd81bff84f2b857754f057d4f4d5
# curl --url https://polygon-mainnet.infura.io/v3/535fdd81bff84f2b857754f057d4f4d5 \
#   -X POST \
#   -H "Content-Type: application/json" \
#   -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# https://rpc-mumbai.maticvigil.com

# https://mumbai.polygonscan.com/  