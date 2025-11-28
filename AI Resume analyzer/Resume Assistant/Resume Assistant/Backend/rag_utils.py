import re
from typing import Tuple, List

# Minimal role->skills map (extend this as you like)
ROLE_SKILLS = {
    "data scientist": ["python", "pandas", "numpy", "scikit-learn", "sklearn", "ml", "machine learning", "deep learning", "tensorflow", "pytorch", "statistics", "model deployment"],
    "ai engineer": ["transformers", "pytorch", "tensorflow", "model deployment", "docker", "mlops", "onnx", "huggingface", "vector db", "r&d"],
    "full stack developer": ["react", "node", "node.js", "express", "django", "flask", "sql", "postgres", "mongodb", "docker", "graphql"],
    # fallback general skills
    "default": ["communication", "teamwork", "problem solving"]
}

def retrieve_context(role: str) -> str:
    if not role:
        return ", ".join(ROLE_SKILLS.get("default"))
    key = role.lower().strip()
    # find closest key
    for k in ROLE_SKILLS.keys():
        if k in key or key in k:
            return ", ".join(ROLE_SKILLS[k])
    return ", ".join(ROLE_SKILLS.get("default"))

def simple_match_score(resume: str, context: str) -> int:
    """
    Returns integer percentage of matched keywords from context.
    """
    if not context:
        return 0
    resume_low = resume.lower()
    keywords = [k.strip() for k in context.split(",") if k.strip()]
    matched = 0
    for kw in keywords:
        # treat multi-word keywords and words the same
        if kw.lower() in resume_low:
            matched += 1
    score = int((matched / max(1, len(keywords))) * 100)
    return score

def extract_skills_from_text(resume: str, context: str) -> Tuple[List[str], List[str]]:
    """
    Return (matched_skills, missing_skills) comparing resume to context keywords.
    """
    resume_low = resume.lower()
    keywords = [k.strip().lower() for k in context.split(",") if k.strip()]
    matched = []
    missing = []
    for kw in keywords:
        # use word-boundary search for single tokens, fallback to substring
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, resume_low):
            matched.append(kw)
        else:
            # Also check substring (helpful for "node" vs "node.js")
            if kw in resume_low:
                matched.append(kw)
            else:
                missing.append(kw)
    return matched, missing
