import streamlit as st
import requests
import pdfplumber
import docx2txt
import base64
from io import BytesIO

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Resume / Job Assistant", layout="wide", initial_sidebar_state="collapsed")

# ---------------- STYLES ----------------
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg,#07111a,#0b1520); color: #e8eef1; }
    .big-title { font-size:48px; color: #00ffd5; font-weight:800; text-align:center; margin-bottom:0;}
    .subtitle { color: #b9c2c8; text-align:center; margin-top:5px; margin-bottom:20px }
    .card { background: rgba(255,255,255,0.03); border-radius:12px; padding:18px; margin-bottom:16px; }
    .accent { color: #ffd166; font-weight:700; }
    .skill-pill { display:inline-block; border-radius:12px; padding:6px 10px; margin:4px; background:#14232b; border: 1px solid #1e9bd1; color:#dff7ff }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='big-title'>Resume / Job Assistant — Demo</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Paste your resume or upload multiple files (PDF / DOCX / TXT)</div>", unsafe_allow_html=True)

# ---------------- BACKEND URL ----------------
BACKEND = "http://localhost:8000"

# ---------------- LAYOUT ----------------
left_col, right_col = st.columns([2, 1])

with left_col:
    with st.expander("Upload files (multiple allowed) — PDF, DOCX, TXT", expanded=True):
        uploaded_files = st.file_uploader("Choose files", type=["pdf", "docx", "txt"], accept_multiple_files=True)

    st.markdown("---")
    st.write("Or paste your resume text below:")
    paste_text = st.text_area("", height=220, placeholder="Paste your resume content or bullets here (optional)")

    role = st.text_input("Target role (e.g., Data Scientist)", placeholder="e.g., Data Scientist")

    analyze_btn = st.button("Analyze", key="analyze")

with right_col:
    st.markdown("<div class='card'><b>Tips</b><ul><li>Upload multiple files or paste text</li><li>PDF viewer appears if you upload a PDF</li><li>Skill extraction + progress shown</li></ul></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><b>Controls</b><p>Make sure backend (FastAPI) is running at <code>http://localhost:8000</code>.</p></div>", unsafe_allow_html=True)

# ---------------- UTIL: extract text from uploaded file (client-side) ----------------
def extract_text_client(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        try:
            # pdfplumber works with a file-like object
            with pdfplumber.open(uploaded_file) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
                return "\n".join(pages)
        except Exception:
            try:
                # fallback: read raw text (some PDFs aren't text-extractable)
                return uploaded_file.getvalue().decode("utf-8", errors="ignore")
            except Exception:
                return ""
    elif name.endswith(".docx"):
        try:
            return docx2txt.process(uploaded_file)
        except Exception:
            return ""
    else:
        try:
            return uploaded_file.getvalue().decode("utf-8", errors="ignore")
        except Exception:
            return ""

# ---------------- UTIL: show PDF in page ----------------
def show_pdf(file_bytes: bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="450" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ---------------- ANALYZE ACTION ----------------
if analyze_btn:
    # Prepare text to send to backend
    combined_text = ""
    # prefer uploaded files; if none, use pasted text
    if uploaded_files:
        # Show PDF viewer for first pdf if any
        first_pdf_shown = False
        for f in uploaded_files:
            # extract client-side for quick local preview + also include in payload
            txt = extract_text_client(f)
            combined_text += "\n" + (txt or "")
            if (not first_pdf_shown) and f.name.lower().endswith(".pdf"):
                try:
                    show_pdf(f.getvalue())
                    first_pdf_shown = True
                except Exception:
                    pass

        # call backend multi-file endpoint with file upload
        files_payload = []
        for f in uploaded_files:
            files_payload.append(("files", (f.name, f.getvalue(), f.type or "application/octet-stream")))

        data = {"role": role}
        with st.spinner("Uploading files and analyzing..."):
            try:
                resp = requests.post(f"{BACKEND}/analyze-multiple", files=files_payload, data=data, timeout=60)
                resp.raise_for_status()
                result = resp.json()
            except Exception as e:
                st.error(f"Backend request failed: {e}")
                result = None

    elif paste_text.strip():
        combined_text = paste_text
        payload = {"resume_text": combined_text, "target_role": role}
        with st.spinner("Analyzing pasted text..."):
            try:
                resp = requests.post(f"{BACKEND}/analyze-text", json=payload, timeout=30)
                resp.raise_for_status()
                result = resp.json()
            except Exception as e:
                st.error(f"Backend request failed: {e}")
                result = None
    else:
        st.error("Please upload files or paste resume text.")
        result = None

    # ---------------- SHOW RESULTS ----------------
    if result:
        score = result.get("match_score", 0)
        matched = result.get("matched_skills", [])
        missing = result.get("missing_skills", [])
        suggested = result.get("suggested_context", "")

        st.markdown("<hr/>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Match Score")
            st.metric(label="Overall fit", value=f"{score} %")
            progress = st.progress(0)
            # animate progress gently
            for i in range(0, score + 1, max(1, int(score/10) or 1)):
                progress.progress(i)
        with col2:
            st.subheader("Quick summary")
            st.write(f"**Role context:** {suggested}")

        st.markdown("### ✅ Matched skills")
        if matched:
            for s in matched:
                st.markdown(f"<span class='skill-pill'>{s}</span>", unsafe_allow_html=True)
        else:
            st.info("No matched skills found.")

        st.markdown("### ⚠️ Missing / Suggested skills to add")
        if missing:
            for s in missing:
                st.markdown(f"<span class='skill-pill' style='background:#3a1f2b;border:1px solid #ff6b6b'>{s}</span>", unsafe_allow_html=True)
        else:
            st.success("No missing skills — great!")

        st.markdown("---")
        st.subheader("Actionable suggestions")
        st.write("- Add missing skill keywords exactly as used in job descriptions (e.g., `pandas`, `docker`, `react`).")
        st.write("- Expand short bullets with measurable impact and tools used.")
        st.write("- If you uploaded a PDF, preview is shown above. If it didn’t render, it might be scanned or image-only PDF.")

