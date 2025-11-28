# backend/ingest.py
import os
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams
from sentence_transformers import SentenceTransformer

MODEL = 'all-MiniLM-L6-v2'
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
COLLECTION = 'resume_domain'


client = QdrantClient(':memory:')
model = SentenceTransformer(MODEL)

chunks = []
for fname in sorted(os.listdir(DATA_DIR)):
    path = os.path.join(DATA_DIR, fname)
    if not os.path.isfile(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            text = line.strip()
            if text:
                chunks.append({'id': f"{fname}:{i}", 'text': text, 'source': fname})

if not chunks:
    print('No data found in', DATA_DIR)
    raise SystemExit(1)

print('Embedding', len(chunks), 'chunks with', MODEL)
texts = [c['text'] for c in chunks]
vectors = model.encode(texts).tolist()

client.recreate_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=len(vectors[0]), distance='Cosine')
)

points = []
for i, c in enumerate(chunks):
    points.append({'id': i, 'vector': vectors[i], 'payload': {'text': c['text'], 'source': c['source']}})

client.upsert(collection_name=COLLECTION, points=points)
print('Ingested', len(points), 'points into collection', COLLECTION)
