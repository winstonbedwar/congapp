import spacy
from sentence_transformers import SentenceTransformer, util
import firebase_admin
from firebase_admin import credentials, initialize_app, db


cred = credentials.Certificate("C:/Users/vijet/Downloads/orwell-ea558-firebase-adminsdk-fbsvc-3589223810.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orwell-ea558-default-rtdb.firebaseio.com/'
})
# Load Spacy and BERT
nlp = spacy.load("en_core_web_trf")
model = SentenceTransformer('all-MiniLM-L6-v2')

text = ("Power Plant Reliability Act of 2025")
text = text.replace('"', "'")

doc = nlp(text)
entities_filtered = [ent for ent in doc.ents if ent.label_ != "DATE"]
entities = set(ent.text for ent in entities_filtered)

# 2. Extract filtered noun chunks
filtered_chunks = []
for chunk in doc.noun_chunks:
    if chunk.root.text.lower() in nlp.Defaults.stop_words:
        continue
    if chunk[0].pos_ == "DET":
        continue
    filtered_chunks.append(chunk.text)

# Combine unique candidates (NER + noun chunks)
candidates = list(set(entities).union(set(filtered_chunks)))

# 3. Embed full text and candidates
doc_emb = model.encode(text, convert_to_tensor=True)
cand_embs = model.encode(candidates, convert_to_tensor=True)

cos_scores = util.cos_sim(cand_embs, doc_emb)
if len(candidates) == 1:
    cos_scores = [cos_scores.item()]
else:
    cos_scores = cos_scores.squeeze().cpu().tolist()

ranked_phrases = sorted(zip(candidates, cos_scores), key=lambda x: x[1], reverse=True)

# Show ranked phrases with similarity scores
for phrase, score in ranked_phrases:
    print(f"{phrase} ({score:.3f})")

ranked_data = []

for phrase, score in ranked_phrases:
    ranked_data.append({
        "phrase": phrase,
        "score": float(score)
    })

ref = db.reference('ranked_keywords')  


new_entry = ref.push({
    'original_text': text,
    'keywords': ranked_data
})
