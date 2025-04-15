import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

# Ensure necessary resources are downloaded
nltk.download("stopwords")
nltk.download("wordnet")

# Load English stopwords
stop_words = set(stopwords.words("english"))

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()

def preprocess_text(text):
    """
    Removes stopwords, special characters, and applies lemmatization to the given text.
    """
    text = text.lower()  # Convert to lowercase
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)  # Remove special characters
    words = text.split()
    
    # Remove stopwords and apply lemmatization
    processed_words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    
    return " ".join(processed_words)
