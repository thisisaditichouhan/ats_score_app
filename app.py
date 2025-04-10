import streamlit as st
import docx2txt
import fitz  # PyMuPDF
import spacy
import spacy.cli
import re

# ✅ Download & load model safely (Streamlit Cloud-friendly)
spacy.cli.download("en_core_web_md")
nlp = spacy.load("en_core_web_md")

# ====== Streamlit Page Setup ======
st.set_page_config(page_title="ATS Resume Score App", layout="wide")
st.title("📊 ATS Resume Score Calculator with Insights")

# ====== File Extraction Helpers ======

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_docx(file):
    return docx2txt.process(file)

def extract_text_from_txt(file):
    return str(file.read(), "utf-8")

def extract_text(file):
    if file.name.endswith(".pdf"):
        return extract_text_from_pdf(file)
    elif file.name.endswith(".docx"):
        return extract_text_from_docx(file)
    elif file.name.endswith(".txt"):
        return extract_text_from_txt(file)
    else:
        return ""

# ====== Phrase Extraction Using spaCy ======
def get_phrases(text):
    doc = nlp(text)
    keywords = set()
    for chunk in doc.noun_chunks:
        phrase = chunk.text.strip().lower()
        if len(phrase.split()) > 1:
            keywords.add(phrase)
    for ent in doc.ents:
        keywords.add(ent.text.strip().lower())
    return list(keywords)

# ====== Similarity Calculation ======
def calculate_similarity(jd_phrases, resume_text, threshold=0.6):
    resume_doc = nlp(resume_text)
    matched = []
    missing = []
    for phrase in jd_phrases:
        phrase_doc = nlp(phrase)
        sim = phrase_doc.similarity(resume_doc)
        if sim >= threshold:
            matched.append((phrase, round(sim, 2)))
        else:
            missing.append((phrase, round(sim, 2)))
    return matched, missing

# ====== Streamlit UI ======

st.subheader("📄 Resume Input")
resume_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
resume_text_input = st.text_area("Or paste resume text here:")

st.subheader("🧾 Job Description Input")
jd_file = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
jd_text_input = st.text_area("Or paste JD text here:")

if st.button("🔍 Analyze Resume"):
    with st.spinner("Analyzing resume, please wait..."):
        # Load resume
        resume_text = ""
        if resume_file:
            resume_text = extract_text(resume_file)
        elif resume_text_input:
            resume_text = resume_text_input

        # Load JD
        jd_text = ""
        if jd_file:
            jd_text = extract_text(jd_file)
        elif jd_text_input:
            jd_text = jd_text_input

        if resume_text.strip() and jd_text.strip():
            jd_phrases = get_phrases(jd_text)
            matched, missing = calculate_similarity(jd_phrases, resume_text)

            score = int((len(matched) / len(jd_phrases)) * 100) if jd_phrases else 0

            # Result Section
            st.subheader("📈 ATS Match Score")
            st.progress(score)
            st.metric("Match Score", f"{score}/100")

            st.subheader("✅ Matched Key Phrases")
            if matched:
                st.success(", ".join([kw for kw, _ in matched]))
            else:
                st.warning("No relevant phrases matched the resume.")

            st.subheader("📌 Suggestions to Improve Resume")
            if missing:
                st.info("Consider including these key phrases (or their concepts):")
                for kw, sim in sorted(missing, key=lambda x: x[1], reverse=True):
                    st.write(f"• {kw}  (similarity: {sim})")
            else:
                st.success("Excellent! Your resume is highly aligned with the job description.")
        else:
            st.warning("Please provide both Resume and JD (upload or paste).")
