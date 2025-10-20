from sentence_transformers import SentenceTransformer, util
import json
import firebase_admin
from firebase_admin import credentials, initialize_app, db
import torch

# Firebase setup
cred = credentials.Certificate("./orwell-ea558-firebase-adminsdk-fbsvc-3589223810.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orwell-ea558-default-rtdb.firebaseio.com/'
})

# Load articles
with open("articles.json", "r") as f:
    data = json.load(f)

articles = data.get("articles", [])
TEXT = data.get("query", "")


# Initialize model and themes
model = SentenceTransformer('all-MiniLM-L6-v2')
themes = ["Economy", "Human Rights", "Environment", "Defense", "Healthcare", "Education"]
theme_embeddings = model.encode(themes, convert_to_tensor=True)

# Collect article texts by source
source_texts = {
    "bbc.com": [],
    "reuters.com": []
}

for article in articles:
    url = article.get('url', '')
    if "bbc.com" in url:
        source_texts["bbc.com"].append(article.get("title", "") + " " + article.get("description", ""))
    elif "reuters.com" in url:
        source_texts["reuters.com"].append(article.get("title", "") + " " + article.get("description", ""))

# Function to compute top themes
def compute_top_themes(texts, k=2):
    if not texts:
        return []

    # Get embeddings for each article
    embeddings = model.encode(texts, convert_to_tensor=True)

    # Average embeddings
    avg_embedding = torch.mean(embeddings, dim=0)

    # Similarity with themes
    cos_scores = util.cos_sim(avg_embedding, theme_embeddings)[0]

    # Get top themes
    top_results = cos_scores.topk(k=k)

    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        results.append({
            "theme": themes[idx],
            "score": float(score)
        })
    return results

# Compute themes per source
bbc_themes = compute_top_themes(source_texts["bbc.com"])
reuters_themes = compute_top_themes(source_texts["reuters.com"])

 
sentiment_data = {
        "bill": TEXT,
        "theme_bbc": bbc_themes,
        "theme_reuter":reuters_themes
    }


# Print results
print("\nBBC Top Themes:")
for item in bbc_themes:
    print(f"- {item['theme']} (Score: {item['score']:.4f})")

print("\nReuters Top Themes:")
for item in reuters_themes:
    print(f"- {item['theme']} (Score: {item['score']:.4f})")

# Upload to Firebase
ref = db.reference('themes')

ref.push(sentiment_data)


