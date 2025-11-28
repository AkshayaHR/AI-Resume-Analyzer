from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from rag_utils import retrieve_context, simple_match_score, extract_skills_from_text
import uvicorn

app = FastAPI()

# Allow CORS so Streamlit (frontend) can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    resume_text: str
    target_role: str

@app.post("/analyze-text")
def analyze_text(req: AnalyzeRequest):
    context = retrieve_context(req.target_role)
    match_score = simple_match_score(req.resume_text, context)
    matched_skills, missing_skills = extract_skills_from_text(req.resume_text, context)
    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "suggested_context": context
    }

@app.post("/analyze-multiple")
async def analyze_multiple(files: List[UploadFile] = File(...), role: str = Form(...)):
    # Read and combine text from all files
    combined_text = ""
    for f in files:
        raw = await f.read()
        try:
            text = raw.decode("utf-8")
        except Exception:
            # if binary (like pdf) just decode using latin-1 fallback
            text = raw.decode("latin-1", errors="ignore")
        combined_text += "\n" + text

    context = retrieve_context(role)
    match_score = simple_match_score(combined_text, context)
    matched_skills, missing_skills = extract_skills_from_text(combined_text, context)
    return {
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "suggested_context": context
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
