from transformers import pipeline
import json
import requests     
from collections import defaultdict

import firebase_admin
from firebase_admin import credentials, initialize_app, db

cred = credentials.Certificate("./orwell-ea558-firebase-adminsdk-fbsvc-3589223810.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orwell-ea558-default-rtdb.firebaseio.com/'
})



with open("articles.json", "r") as f:
    data = json.load(f)


ref = db.reference('sentiment')  


TEXT = data.get("query", "")
articles = data.get("articles",[])
print(f"Query phrase: {TEXT}")
sentiment_data = {
    "query_text": TEXT
}


sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

# Map model labels to human-friendly labels and numeric values
label_map = {
    "LABEL_0": ("Negative", 0),
    "LABEL_1": ("Neutral", 1),
    "LABEL_2": ("Positive", 2)
}

# Analyze sentiment and attach it to articles
for i, article in enumerate(articles):
    text_to_analyze = article.get("title", "") + " " + article.get("description", "")
    if text_to_analyze.strip() == "":
        continue

    result = sentiment_analyzer(text_to_analyze)[0]
    model_label = result['label']
    confidence = result['score']

    sentiment_label, numeric_value = label_map.get(model_label, ("Neutral", 1))

    article['sentiment_label'] = sentiment_label
    article['sentiment_confidence'] = confidence
    article['sentiment_numeric'] = numeric_value

# Group scores by source
source_scores = defaultdict(list)
source_confidences = defaultdict(list)

for article in articles:
    url = article.get('url', '')
    numeric_score = article.get('sentiment_numeric')
    confidence_score = article.get('sentiment_confidence')
    
    if numeric_score is None or not url:
        continue
    
    if "bbc.com" in url:
        source = "bbc.com"
    elif "reuters.com" in url:
        source = "reuters.com"
    else:
        continue

    source_scores[source].append(numeric_score)
    source_confidences[source].append(confidence_score)


# # Print results per source
for source in source_scores:
    avg_score = sum(source_scores[source]) / len(source_scores[source])
    avg_confidence = sum(source_confidences[source]) / len(source_confidences[source])
    
    key = source.replace('.', '_')
    sentiment_data[key] = {
        "average_sentiment": round(avg_score, 3),
        "average_confidence": round(avg_confidence, 3)
    }




    
    print(f"\nSource: {source}")
    print(f"  Average Sentiment (0=Neg, 1=Neu, 2=Pos): {avg_score:.3f}")
    print(f"  Average Confidence: {avg_confidence:.3f}")


ref.push(sentiment_data)


#next up: push sentiment values to database so frontend can use it. AFTER THAT also figure out keywords detection (probably POS that you have to do)
#last: figure out how to automate this ????


# with open("articles.json", "r") as f:
#     articles = json.load(f)

#     sentiment_analyzer = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
#     for i, article in enumerate(articles):
#         text_to_analyze = article.get("title", "") + " " + article.get("description", "")
#         if text_to_analyze.strip() == "": 
#          continue
    
#     result = sentiment_analyzer(text_to_analyze)[0]
#     label = result['label']
#     score = result['score']

#     print(f"Article {i+1}:")
#     print(f"Title: {article.get('title', 'N/A')}")
#     print(f"Sentiment: {label} (score: {score:.2f})\n")

    # for article in articles:
    #     print(article['title']) 