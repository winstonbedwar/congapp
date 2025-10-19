import spacy
from sentence_transformers import SentenceTransformer, util
import firebase_admin
from firebase_admin import credentials, initialize_app, db

cred = credentials.Certificate("C:/Users/vijet/Downloads/orwell-ea558-firebase-adminsdk-fbsvc-3589223810.json")

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://orwell-ea558-default-rtdb.firebaseio.com/'
})


# Load spaCy and SentenceTransformer models
nlp = spacy.load("en_core_web_trf")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Input text
text = "Small Cemetery Conveyance Act"
text = text.replace('"', "'")

# Process text with spaCy
doc = nlp(text)

# 1. Extract named entities (exclude DATE)
entities_filtered = [ent for ent in doc.ents if ent.label_ != "DATE"]
entities = set(ent.text.strip() for ent in entities_filtered)

# 2. Extract noun chunks (keep spaCy Span objects)
filtered_chunks = []
for chunk in doc.noun_chunks:
    if chunk.root.text.lower() in nlp.Defaults.stop_words:
        continue
    if chunk[0].pos_ == "DET":
        continue
    filtered_chunks.append(chunk)

# 3. Extract subphrases from longer noun chunks
subphrases = []
for chunk in filtered_chunks:
    words = chunk.text.split()
    if len(words) > 2:
        subphrases.append(" ".join(words[:2]))       # First two words
        subphrases.append(chunk.root.text.strip())   # Head noun

# 4. Prepare filtered_chunks text list for candidates
filtered_chunks_text = [chunk.text.strip() for chunk in filtered_chunks]

# 5. Combine all unique candidates
candidates = list(set(entities) | set(filtered_chunks_text) | set(subphrases))

# 6. Embed original text and candidate phrases
doc_emb = model.encode(text, convert_to_tensor=True)
cand_embs = model.encode(candidates, convert_to_tensor=True)

# 7. Compute cosine similarity scores
cos_scores = util.cos_sim(cand_embs, doc_emb)
if len(candidates) == 1:
    cos_scores = [cos_scores.item()]
else:
    cos_scores = cos_scores.squeeze().cpu().tolist()

# 8. Rank candidates by similarity descending
ranked_phrases = sorted(zip(candidates, cos_scores), key=lambda x: x[1], reverse=True)

# 9. Print ranked key phrases
print("Ranked Phrases:\n")
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



